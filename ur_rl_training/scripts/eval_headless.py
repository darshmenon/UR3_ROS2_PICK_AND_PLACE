"""
Headless policy evaluation — no GUI, no ROS.

Usage:
    python3 scripts/eval_headless.py --model <path/to/best_model.zip> [--episodes 50]
"""

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np

# The system triton package segfaults on import when torch builds an Adam
# optimizer (SAC._build). Block it before torch/stable_baselines3 load —
# CPU eval here never needs triton kernels anyway. Same fix as
# ur_rl_training/policy_node.py.
sys.modules["triton"] = None

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from envs.ur3_pick_place_env import UR3PickPlaceEnv
from stable_baselines3 import SAC


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model",    type=str, required=True)
    p.add_argument("--episodes", type=int, default=50)
    p.add_argument("--curriculum", type=str, default="grasp_focus",
                   choices=["none", "grasp_focus"])
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def main():
    args  = parse_args()
    model = SAC.load(args.model)
    env   = UR3PickPlaceEnv(curriculum_mode=args.curriculum,
                            domain_randomisation=False)

    obs_rms = None
    norm_path = Path(args.model).parent / "vecnormalize.pkl"
    if norm_path.exists():
        with open(norm_path, "rb") as f:
            obs_rms = pickle.load(f).obs_rms
        print(f"VecNormalize loaded from {norm_path}")

    rewards        = []
    ep_lengths     = []
    max_phase      = []
    phase_counts   = {0: 0, 1: 0, 2: 0, 3: 0}
    successes      = 0

    for ep in range(args.episodes):
        obs, _ = env.reset(seed=args.seed + ep)
        total_r = 0.0
        steps   = 0
        peak_ph = 0
        done    = False

        while not done:
            if obs_rms is not None:
                obs = np.clip((obs - obs_rms.mean) / np.sqrt(obs_rms.var + 1e-8),
                              -10.0, 10.0).astype(np.float32)
            action, _ = model.predict(obs, deterministic=True)
            obs, r, terminated, truncated, info = env.step(action)
            total_r += r
            steps   += 1
            ph = int(info.get("phase", 0))
            if ph > peak_ph:
                peak_ph = ph
            done = terminated or truncated
            if terminated:
                successes += 1

        rewards.append(total_r)
        ep_lengths.append(steps)
        max_phase.append(peak_ph)
        phase_counts[peak_ph] = phase_counts.get(peak_ph, 0) + 1

    env.close()

    print(f"\n=== Headless Eval: {args.model} ===")
    print(f"Episodes : {args.episodes}")
    print(f"Mean reward  : {np.mean(rewards):.2f} ± {np.std(rewards):.2f}")
    print(f"Median reward: {np.median(rewards):.2f}")
    print(f"Max reward   : {np.max(rewards):.2f}")
    print(f"Min reward   : {np.min(rewards):.2f}")
    print(f"Mean ep len  : {np.mean(ep_lengths):.1f} steps")
    print(f"\nSuccess rate (full place): {successes}/{args.episodes}  ({100*successes/args.episodes:.1f}%)")
    print(f"\nPeak phase reached:")
    for ph, label in [(0, "reach"), (1, "grasp"), (2, "lift"), (3, "carry/place")]:
        count = phase_counts.get(ph, 0)
        print(f"  Phase {ph} ({label:12s}): {count:3d} eps  ({100*count/args.episodes:.1f}%)")


if __name__ == "__main__":
    main()
