"""DAgger for the MuJoCo pick-and-place environment (CPU only, no reward needed).

Behaviour cloning on the scripted expert's demos drifts: the learned policy visits states the expert never did. DAgger
fixes that by running the LEARNED policy and asking the scripted expert (scripts/expert_demos.py) what it would do in
each visited state, then retraining on all the data collected so far.

Run from ur_rl_training/:
    python3 scripts/dagger.py --demos ~/ur3_rl_demos/expert.npz --iters 6 --episodes 20 --out ~/ur3_rl_demos/dagger.pt

The per-iteration success rate is that of the learned policy alone (iteration 0 is plain behaviour cloning).
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


def make_policy(obs_dim, act_dim):
    return torch.nn.Sequential(
        torch.nn.Linear(obs_dim, 256), torch.nn.ReLU(),
        torch.nn.Linear(256, 256), torch.nn.ReLU(),
        torch.nn.Linear(256, act_dim), torch.nn.Tanh())


def fit(policy, x, y, epochs):
    opt = torch.optim.Adam(policy.parameters(), lr=1e-3)
    for _ in range(epochs):
        perm = torch.randperm(len(x))
        for i in range(0, len(x), 512):
            idx = perm[i:i + 512]
            loss = torch.nn.functional.mse_loss(policy(x[idx]), y[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
    return float(loss.detach())


def rollouts(env, policy, mean, std, episodes, seed, max_steps):
    """Run the learned policy; label every visited state with the expert's action."""
    obs_l, act_l, ok = [], [], 0
    for ep in range(episodes):
        obs, _ = env.reset(seed=seed + ep)
        ex = Expert(env)
        for _ in range(max_steps):
            label = ex.act()
            obs_l.append(obs)
            act_l.append(label)
            with torch.no_grad():
                a = policy(torch.as_tensor((obs - mean) / std, dtype=torch.float32)).numpy()
            obs, _, term, trunc, info = env.step(a)
            if term or trunc:
                ok += bool(term and info.get("success"))
                break
    return np.asarray(obs_l, dtype=np.float32), np.asarray(act_l, dtype=np.float32), ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demos", default=str(Path.home() / "ur3_rl_demos" / "expert.npz"))
    ap.add_argument("--iters", type=int, default=6)
    ap.add_argument("--episodes", type=int, default=20, help="learned-policy episodes per iteration")
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--max-steps", type=int, default=800)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=str(Path.home() / "ur3_rl_demos" / "dagger.pt"))
    args = ap.parse_args()
    torch.set_num_threads(args.threads)

    d = np.load(Path(args.demos).expanduser())
    obs, act = d["obs"].astype(np.float32), d["act"].astype(np.float32)
    mean, std = obs.mean(0), obs.std(0) + 1e-6
    env = UR3PickPlaceEnvV2(curriculum_mode="grasp_focus", domain_randomisation=False)
    policy = make_policy(obs.shape[1], act.shape[1])
    best = -1
    t0 = time.time()
    for it in range(args.iters + 1):
        loss = fit(policy, torch.as_tensor((obs - mean) / std), torch.as_tensor(act), args.epochs)
        new_obs, new_act, ok = rollouts(env, policy, mean, std, args.episodes, args.seed + 1000 * it, args.max_steps)
        print(f"iter {it}: data {len(obs):,}, fit loss {loss:.4f}, learned policy success {ok}/{args.episodes}, "
              f"+{len(new_obs):,} labelled states, {time.time() - t0:.0f} s", flush=True)
        if ok >= best:
            best = ok
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save({"policy": policy.state_dict(), "mean": mean, "std": std, "success": ok / args.episodes},
                       args.out)
        obs, act = np.concatenate([obs, new_obs]), np.concatenate([act, new_act])
    print(f"best {best}/{args.episodes}; saved {args.out}")


if __name__ == "__main__":
    main()
