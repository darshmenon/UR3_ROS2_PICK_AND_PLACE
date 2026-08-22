#!/usr/bin/env python3
"""
Evaluate the trained RL (SAC) pick-place policy on the MuJoCo environment.

Usage:
    python3 testing/eval_rl_policy.py                        # best_model from training run
    python3 testing/eval_rl_policy.py --model path/to/best_model.zip --episodes 20
    python3 testing/eval_rl_policy.py --render                # opens a viewer window

No ROS needed — pure MuJoCo eval.
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np

# The system triton package segfaults on import when torch builds an Adam
# optimizer (SAC._build). Block it before torch/stable_baselines3 load —
# CPU eval here never needs triton kernels anyway. Same fix as
# ur_rl_training/policy_node.py.
sys.modules["triton"] = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ur_rl_training"))

BEST_MODEL = ROOT / "ur_rl_training" / "models" / "checkpoints" / "ur3_pick_place_20260518_0922" / "best_model.zip"
VECNORM    = ROOT / "ur_rl_training" / "models" / "checkpoints" / "ur3_pick_place_20260518_0922" / "vecnormalize.pkl"


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--model",    default=str(BEST_MODEL))
    p.add_argument("--vecnorm",  default=str(VECNORM) if VECNORM.exists() else "")
    p.add_argument("--episodes", type=int, default=20)
    p.add_argument("--render",   action="store_true")
    p.add_argument("--seed",     type=int, default=0)
    return p.parse_args()


def main():
    args = parse_args()

    print(f"Loading env…")
    from envs.ur3_pick_place_env import UR3PickPlaceEnv
    from stable_baselines3 import SAC
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    render_mode = "human" if args.render else None
    raw_env = DummyVecEnv([lambda: UR3PickPlaceEnv(render_mode=render_mode)])

    if args.vecnorm and Path(args.vecnorm).exists():
        print(f"Loading VecNormalize from {args.vecnorm}")
        env = VecNormalize.load(args.vecnorm, raw_env)
        env.training = False
        env.norm_reward = False
    else:
        env = raw_env
        print("No VecNormalize found — running without obs normalisation")

    print(f"Loading model from {args.model}")
    model = SAC.load(args.model, env=env)

    print(f"\nRunning {args.episodes} evaluation episodes…\n")

    successes  = []
    rewards    = []
    lengths    = []
    phases     = []
    cycle_times = []

    PHASE_NAMES = {0: "reach", 1: "grasp", 2: "lift", 3: "place"}

    for ep in range(args.episodes):
        obs = env.reset()
        ep_reward = 0.0
        ep_steps  = 0
        peak_phase = 0
        t0 = time.time()

        while True:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)

            ep_reward += float(reward[0])
            ep_steps  += 1

            ph = info[0].get("phase", 0)
            if ph > peak_phase:
                peak_phase = ph

            if done[0]:
                success = info[0].get("success", False)
                elapsed = time.time() - t0
                successes.append(success)
                rewards.append(ep_reward)
                lengths.append(ep_steps)
                phases.append(peak_phase)
                cycle_times.append(elapsed)

                status = "✓ SUCCESS" if success else f"✗ phase={PHASE_NAMES.get(peak_phase, peak_phase)}"
                print(f"  ep {ep+1:>2}/{args.episodes}  {status:<20}  reward={ep_reward:>8.1f}  steps={ep_steps:>4}  {elapsed:.1f}s")
                break

    # ── summary ──────────────────────────────────────────────────────────────
    n = len(successes)
    sr = sum(successes) / n * 100
    print(f"\n{'═'*60}")
    print(f"  Episodes:      {n}")
    print(f"  Success rate:  {sr:.1f}%  ({sum(successes)}/{n})")
    print(f"  Avg reward:    {np.mean(rewards):.1f}  (std {np.std(rewards):.1f})")
    print(f"  Avg steps:     {np.mean(lengths):.0f}  (max {np.max(lengths)})")
    print(f"  Avg time:      {np.mean(cycle_times):.2f}s")

    phase_dist = {PHASE_NAMES[k]: phases.count(k) for k in range(4)}
    print(f"\n  Peak-phase distribution:")
    for name, count in phase_dist.items():
        bar = "█" * count
        print(f"    {name:<8}  {bar:<20}  {count}")

    print(f"{'═'*60}")

    env.close()
    return 0 if sr >= 50 else 1


if __name__ == "__main__":
    sys.exit(main())
