#!/usr/bin/env python3
"""
Detailed per-step diagnostic for the RL policy.

Shows gripper position, object lift, contact state, and phase transition
every 50 steps so we can see exactly why it's not completing the task.

Usage:
    python3 testing/diagnose_rl.py --episodes 3
    python3 testing/diagnose_rl.py --render       # opens viewer
"""
import argparse, sys
from pathlib import Path
import numpy as np

# The system triton package segfaults on import when torch builds an Adam
# optimizer (SAC._build). Block it before torch/stable_baselines3 load —
# CPU here never needs triton kernels anyway. Same fix as
# ur_rl_training/policy_node.py.
sys.modules["triton"] = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ur_rl_training"))

CKPT    = ROOT / "ur_rl_training/models/checkpoints/ur3_pick_place_20260518_0922/best_model.zip"
VECNORM = ROOT / "ur_rl_training/models/checkpoints/ur3_pick_place_20260518_0922/vecnormalize.pkl"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--episodes", type=int, default=3)
    p.add_argument("--render",   action="store_true")
    args = p.parse_args()

    from envs.ur3_pick_place_env import UR3PickPlaceEnv
    from stable_baselines3 import SAC
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
    import mujoco

    render_mode = "human" if args.render else None
    raw = DummyVecEnv([lambda: UR3PickPlaceEnv(render_mode=render_mode)])
    env = VecNormalize.load(str(VECNORM), raw)
    env.training = False; env.norm_reward = False

    model = SAC.load(str(CKPT), env=env)

    for ep in range(args.episodes):
        obs = env.reset()
        print(f"\n{'═'*70}")
        print(f"Episode {ep+1}")
        print(f"{'─'*70}")
        print(f"  {'step':>5}  {'phase':>5}  {'grip_q':>7}  {'obj_z':>7}  "
              f"{'obj_lift':>8}  {'ee→obj':>7}  {'contact':>8}  {'reward':>8}")

        ep_reward = 0
        for step in range(2001):
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            ep_reward += float(reward[0])

            # Read raw env state (through VecNormalize wrapper)
            inner = env.venv.envs[0]
            grip  = float(inner.data.qpos[inner._grip_qpos])
            obj   = inner.data.xpos[inner._obj_body].copy()
            ee    = inner.data.site_xpos[inner._ee_site].copy()
            init_z = float(inner._obj_init_pos[2])
            obj_lift = obj[2] - init_z
            ee_obj   = float(np.linalg.norm(ee - obj))
            lc, rc   = inner._contact_state()
            contact  = "LR" if (lc and rc) else ("L" if lc else ("R" if rc else "--"))

            if step % 100 == 0 or done[0] or info[0].get("phase", 1) != 1:
                print(f"  {step:>5}  {info[0].get('phase',1):>5}  {grip:>7.3f}  "
                      f"{obj[2]:>7.3f}  {obj_lift:>8.4f}  {ee_obj:>7.3f}  "
                      f"{contact:>8}  {float(reward[0]):>8.3f}")

            if done[0]:
                print(f"\n  → Episode ended at step {step}. Total reward: {ep_reward:.1f}")
                break

        # Final state summary
        inner = env.venv.envs[0]
        grip  = float(inner.data.qpos[inner._grip_qpos])
        obj   = inner.data.xpos[inner._obj_body].copy()
        print(f"\n  Final state: grip={grip:.3f} obj={obj} phase={inner._phase}")

    env.close()


if __name__ == "__main__":
    main()
