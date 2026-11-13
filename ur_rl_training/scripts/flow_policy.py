"""Flow-matching policy with action chunks, trained from the scripted expert (CPU only, no reward needed).

The network predicts the next H actions at once from the observation: a velocity field v(x_tau, tau | obs) is trained
so that integrating it from Gaussian noise (tau 0 -> 1) gives an expert action chunk. Acting executes the first K
actions of a chunk, then replans. Chunking cuts the drift that plain behaviour cloning suffers from, and the generative
head also copes with demos that disagree (e.g. different MTC plans for the same scene).

Optionally (--iters) it runs DAgger on top: the flow policy drives, the scripted expert (scripts/expert_demos.py)
labels each visited state, and the model is retrained on everything collected so far.

Run from ur_rl_training/:
    python3 scripts/flow_policy.py --demos ~/ur3_rl_demos/expert.npz --iters 4 --episodes 20
"""
import argparse
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import torch  # noqa: E402

from envs.ur3_pick_place_env_v2 import UR3PickPlaceEnvV2  # noqa: E402
from expert_demos import Expert  # noqa: E402


class FlowNet(torch.nn.Module):
    def __init__(self, obs_dim, act_dim, horizon, hidden=512):
        super().__init__()
        self.out = act_dim * horizon
        self.net = torch.nn.Sequential(
            torch.nn.Linear(obs_dim + self.out + 1, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, hidden), torch.nn.SiLU(),
            torch.nn.Linear(hidden, self.out))

    def forward(self, obs, x, tau):
        return self.net(torch.cat([obs, x, tau], dim=-1))

    @torch.no_grad()
    def sample(self, obs, steps):
        x = torch.randn(len(obs), self.out)
        for i in range(steps):
            tau = torch.full((len(obs), 1), i / steps)
            x = x + self(obs, x, tau) / steps
        return x.clamp(-1, 1)


def split_episodes(obs, act, done):
    ends = np.flatnonzero(done > 0.5)
    eps, start = [], 0
    for e in ends:
        eps.append((obs[start:e + 1], act[start:e + 1]))
        start = e + 1
    if start < len(obs):
        eps.append((obs[start:], act[start:]))
    return eps


def chunk_targets(eps, horizon):
    """For every step the next `horizon` expert actions (padded with the last one at the end of an episode)."""
    xs, ys = [], []
    for o, a in eps:
        pad = np.concatenate([a, np.repeat(a[-1:], horizon - 1, axis=0)])
        for t in range(len(o)):
            xs.append(o[t])
            ys.append(pad[t:t + horizon].reshape(-1))
    return np.asarray(xs, dtype=np.float32), np.asarray(ys, dtype=np.float32)


def train(model, opt, obs_n, chunks, epochs, batch=256):
    x, y = torch.as_tensor(obs_n), torch.as_tensor(chunks)
    for _ in range(epochs):
        perm = torch.randperm(len(x))
        for i in range(0, len(x), batch):
            idx = perm[i:i + batch]
            x1 = y[idx]
            x0 = torch.randn_like(x1)
            tau = torch.rand(len(idx), 1)
            xt = (1 - tau) * x0 + tau * x1
            loss = torch.nn.functional.mse_loss(model(x[idx], xt, tau), x1 - x0)
            opt.zero_grad()
            loss.backward()
            opt.step()
    return float(loss.detach())


def rollouts(env, model, mean, std, episodes, seed, max_steps, horizon, replan, steps):
    """Flow policy drives (first `replan` actions of each chunk); the expert labels every visited state."""
    new, ok = [], 0
    for ep in range(episodes):
        obs, _ = env.reset(seed=seed + ep)
        ex = Expert(env)
        o_l, a_l, queue, finished = [], [], [], False
        for _ in range(max_steps):
            label = ex.act()
            o_l.append(obs)
            a_l.append(label)
            if not queue:
                chunk = model.sample(torch.as_tensor((obs - mean) / std, dtype=torch.float32)[None], steps)
                queue = list(chunk.reshape(horizon, -1).numpy()[:replan])
            obs, _, term, trunc, info = env.step(queue.pop(0))
            if term or trunc:
                ok += bool(term and info.get("success"))
                break
        new.append((np.asarray(o_l, dtype=np.float32), np.asarray(a_l, dtype=np.float32)))
    return new, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demos", default=str(Path.home() / "ur3_rl_demos" / "expert.npz"))
    ap.add_argument("--iters", type=int, default=4, help="DAgger iterations after the first fit (0 = plain cloning)")
    ap.add_argument("--episodes", type=int, default=20, help="flow-policy episodes per iteration (also the eval)")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--horizon", type=int, default=16)
    ap.add_argument("--replan", type=int, default=8)
    ap.add_argument("--flow-steps", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=800)
    ap.add_argument("--seed", type=int, default=2000)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=str(Path.home() / "ur3_rl_demos" / "flow.pt"))
    args = ap.parse_args()
    torch.set_num_threads(args.threads)

    d = np.load(Path(args.demos).expanduser())
    eps = split_episodes(d["obs"].astype(np.float32), d["act"].astype(np.float32), d["done"])
    all_obs = np.concatenate([o for o, _ in eps])
    mean, std = all_obs.mean(0), all_obs.std(0) + 1e-6
    env = UR3PickPlaceEnvV2(curriculum_mode="grasp_focus", domain_randomisation=False)
    model = FlowNet(all_obs.shape[1], d["act"].shape[1], args.horizon)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    best, t0 = -1, time.time()
    for it in range(args.iters + 1):
        x, y = chunk_targets(eps, args.horizon)
        loss = train(model, opt, (x - mean) / std, y, args.epochs)
        new, ok = rollouts(env, model, mean, std, args.episodes, args.seed + 1000 * it, args.max_steps,
                           args.horizon, args.replan, args.flow_steps)
        print(f"iter {it}: {len(x):,} chunks, flow loss {loss:.4f}, flow policy success {ok}/{args.episodes}, "
              f"+{sum(len(o) for o, _ in new):,} labelled states, {time.time() - t0:.0f} s", flush=True)
        if ok >= best:
            best = ok
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save({"model": model.state_dict(), "mean": mean, "std": std, "horizon": args.horizon,
                        "replan": args.replan, "flow_steps": args.flow_steps, "success": ok / args.episodes},
                       args.out)
        eps = eps + new
    print(f"best {best}/{args.episodes}; saved {args.out}")


if __name__ == "__main__":
    main()
