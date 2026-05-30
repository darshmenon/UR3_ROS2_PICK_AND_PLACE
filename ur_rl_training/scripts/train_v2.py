"""
Fast SAC training with the v2 environment (fixed reward shaping).

Run from ur_rl_training/:
    python3 scripts/train_v2.py

Key differences from train.py:
  - Uses UR3PickPlaceEnvV2 (zero reward at >0.12 m, gripper closure bonus)
  - 8 s episode limit (vs 20 s) — faster iteration
  - 16 parallel envs on CPU
  - Smaller net (64×64) — faster inference per step
  - Higher entropy target — more exploration
  - 1 M timesteps with eval every 20 k
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from envs.ur3_pick_place_env_v2 import UR3PickPlaceEnvV2
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import (
    CallbackList, CheckpointCallback, EvalCallback,
)
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecMonitor, VecNormalize

LOG_ROOT   = str(REPO_ROOT / "logs")
MODEL_ROOT = str(REPO_ROOT / "models" / "checkpoints")


def make_env(curriculum_mode="grasp_focus", seed=0):
    def _init():
        env = UR3PickPlaceEnvV2(curriculum_mode=curriculum_mode, domain_randomisation=True)
        env.reset(seed=seed)
        return env
    return _init


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--timesteps",   type=int,   default=1_000_000)
    p.add_argument("--n_envs",      type=int,   default=16)
    p.add_argument("--eval_freq",   type=int,   default=50_000)
    p.add_argument("--n_eval_ep",   type=int,   default=5)
    p.add_argument("--curriculum",  default="grasp_focus",
                   choices=["none", "grasp_focus"])
    p.add_argument("--resume",      default="",
                   help="Path to a .zip checkpoint to resume from")
    args = p.parse_args()

    run_name  = f"ur3_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ckpt_dir  = os.path.join(MODEL_ROOT, run_name)
    os.makedirs(ckpt_dir, exist_ok=True)

    print(f"Run: {run_name}")
    print(f"Envs: {args.n_envs}  Timesteps: {args.timesteps:,}  Curriculum: {args.curriculum}")

    # ── training env ─────────────────────────────────────────────────────────
    train_raw = SubprocVecEnv([make_env(args.curriculum, seed=i) for i in range(args.n_envs)])
    train_env = VecNormalize(VecMonitor(train_raw), norm_obs=True, norm_reward=True, clip_obs=10.0)

    # ── eval env (no normalise update, no reward norm) ────────────────────────
    eval_raw = DummyVecEnv([make_env("none", seed=9999)])
    eval_env = VecNormalize(VecMonitor(eval_raw), norm_obs=True, norm_reward=False, training=False)
    eval_env.obs_rms = train_env.obs_rms

    # ── model ─────────────────────────────────────────────────────────────────
    policy_kwargs = dict(net_arch=[64, 64])

    if args.resume:
        print(f"Resuming from {args.resume}")
        model = SAC.load(
            args.resume, env=train_env,
            learning_rate=1e-4,
            verbose=1,
            tensorboard_log=LOG_ROOT,
        )
    else:
        model = SAC(
            "MlpPolicy",
            train_env,
            learning_rate=3e-4,
            buffer_size=500_000,
            learning_starts=5_000,
            batch_size=512,
            tau=0.005,
            gamma=0.99,
            train_freq=1,
            gradient_steps=4,
            ent_coef="auto_0.2",   # higher entropy target → more gripper exploration
            target_entropy=-4.0,   # 7-dim action space, ~-N/2
            policy_kwargs=policy_kwargs,
            verbose=1,
            tensorboard_log=LOG_ROOT,
            device="cuda",
        )

    # ── callbacks ──────────────────────────────────────────────────────────────
    checkpoint_cb = CheckpointCallback(
        save_freq=max(args.eval_freq // args.n_envs, 1),
        save_path=ckpt_dir,
        name_prefix="ckpt",
    )

    class SyncNormEval(EvalCallback):
        def _on_step(self):
            eval_env.obs_rms = train_env.obs_rms
            prev = self.best_mean_reward
            res  = super()._on_step()
            if self.best_model_save_path and self.best_mean_reward > prev:
                train_env.save(os.path.join(self.best_model_save_path, "vecnormalize.pkl"))
                eval_env.save(os.path.join(self.best_model_save_path, "eval_vecnormalize.pkl"))
            return res

    eval_cb = SyncNormEval(
        eval_env,
        best_model_save_path=ckpt_dir,
        log_path=ckpt_dir,
        eval_freq=max(args.eval_freq // args.n_envs, 1),
        n_eval_episodes=args.n_eval_ep,
        deterministic=True,
        verbose=1,
    )

    # ── train ─────────────────────────────────────────────────────────────────
    model.learn(
        total_timesteps=args.timesteps,
        callback=CallbackList([checkpoint_cb, eval_cb]),
        tb_log_name=run_name,
        reset_num_timesteps=not bool(args.resume),
    )

    model.save(os.path.join(ckpt_dir, "final_model"))
    train_env.save(os.path.join(ckpt_dir, "vecnormalize.pkl"))
    print(f"\nTraining complete. Model saved to {ckpt_dir}")


if __name__ == "__main__":
    main()
