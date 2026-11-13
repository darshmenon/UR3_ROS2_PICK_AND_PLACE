"""Success rate of a saved DAgger (dagger.pt), flow (flow.pt) or SAC (best_model.zip) policy over many episodes (CPU only).

Run from ur_rl_training/:
    python3 scripts/eval_policy.py --policy ~/ur3_rl_demos/flow.pt --episodes 50
    python3 scripts/eval_policy.py --policy expert --episodes 50      # the scripted expert on the same seeds
"""
import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

sys.modules["triton"] = None   # the system triton package segfaults on import when torch builds an optimizer (SAC load)

import numpy as np  # noqa: E402
import torch  # noqa: E402

from dagger import make_policy  # noqa: E402
from envs.ur3_pick_place_env_v2 import UR3PickPlaceEnvV2  # noqa: E402
from expert_demos import Expert  # noqa: E402
from flow_policy import FlowNet  # noqa: E402


def load_actor(path, obs_dim, act_dim):
    """Returns act(obs) -> action for either checkpoint type (flow: executes chunks, replanning every `replan`)."""
    path = Path(path).expanduser()
    if path.suffix == ".zip":                      # Stable-Baselines3 SAC (train_v2.py) + its VecNormalize stats
        import pickle

        from stable_baselines3 import SAC
        sac = SAC.load(str(path), device="cpu")
        stats = next(p for p in (path.parent / "vecnormalize.pkl", path.parent / "eval_vecnormalize.pkl") if p.exists())
        with open(stats, "rb") as f:
            vn = pickle.load(f)
        eps, clip = vn.epsilon, vn.clip_obs

        def act(obs):
            n = np.clip((obs - vn.obs_rms.mean) / np.sqrt(vn.obs_rms.var + eps), -clip, clip)
            return sac.predict(n.astype(np.float32), deterministic=True)[0]

        act.reset = lambda: None
        return act
    ck = torch.load(path, weights_only=False)
    mean, std = ck["mean"], ck["std"]
    if "model" in ck:
        net = FlowNet(obs_dim, act_dim, ck["horizon"])
        net.load_state_dict(ck["model"])
        queue = []

        def act(obs):
            if not queue:
                chunk = net.sample(torch.as_tensor((obs - mean) / std, dtype=torch.float32)[None], ck["flow_steps"])
                queue.extend(chunk.reshape(ck["horizon"], -1).numpy()[:ck["replan"]])
            return queue.pop(0)

        act.reset = queue.clear
    else:
        net = make_policy(obs_dim, act_dim)
        net.load_state_dict(ck["policy"])

        def act(obs):
            with torch.no_grad():
                return net(torch.as_tensor((obs - mean) / std, dtype=torch.float32)).numpy()

        act.reset = lambda: None
    return act


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=str(Path.home() / "ur3_rl_demos" / "flow.pt"))
    ap.add_argument("--episodes", type=int, default=50)
    ap.add_argument("--seed", type=int, default=9000)
    ap.add_argument("--max-steps", type=int, default=800)
    ap.add_argument("--threads", type=int, default=2)
    args = ap.parse_args()
    torch.set_num_threads(args.threads)
    env = UR3PickPlaceEnvV2(curriculum_mode="grasp_focus", domain_randomisation=False)
    expert = args.policy == "expert"          # the scripted expert itself, on the same start positions
    act = None if expert else load_actor(args.policy, env.observation_space.shape[0], env.action_space.shape[0])
    ok = 0
    for ep in range(args.episodes):
        obs, _ = env.reset(seed=args.seed + ep)
        if expert:
            ex = Expert(env)
            act = lambda _obs, ex=ex: ex.act()  # noqa: E731
        else:
            act.reset()
        for t in range(args.max_steps):
            obs, _, term, trunc, info = env.step(act(obs))
            if term or trunc:
                ok += bool(term and info.get("success"))
                break
        print(f"episode {ep + 1}/{args.episodes}: {ok} successes so far", flush=True)
    p = ok / args.episodes
    se = (p * (1 - p) / args.episodes) ** 0.5
    print(f"{args.policy}: {ok}/{args.episodes} = {p:.0%} (+/- {se:.0%} standard error)")


if __name__ == "__main__":
    main()
