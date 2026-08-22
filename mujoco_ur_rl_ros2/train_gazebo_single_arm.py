"""
Train a single-arm SAC policy that transfers to the Gazebo colored_blocks world.

Arm at origin (local == world frame), 23-dim obs matching shared_arm_policy_node.
Run from repo root:
    python3 scripts/train/train_gazebo_single_arm.py
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
import re

# The system triton package segfaults on import when torch builds an Adam
# optimizer (SAC._build). Block it before torch/stable_baselines3 load —
# CPU training here never needs triton kernels anyway. Same fix as
# ur_rl_training/policy_node.py.
sys.modules["triton"] = None

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from envs.ur_gazebo_single_arm_env import URGazeboSingleArmEnv
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import (
    CallbackList, CheckpointCallback, EvalCallback,
)
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor


LOG_ROOT   = "logs/gazebo_single_arm"
MODEL_ROOT = "models/gazebo_single_arm"


class EvalCallbackWithReplayBuffer(EvalCallback):
    """Save a replay buffer alongside best_model.zip whenever eval finds a new best."""

    def _on_step(self) -> bool:
        previous_best = self.best_mean_reward
        continue_training = super()._on_step()
        if self.best_model_save_path and self.best_mean_reward > previous_best:
            replay_buffer_path = os.path.join(
                self.best_model_save_path,
                "best_model_replay_buffer.pkl",
            )
            self.model.save_replay_buffer(replay_buffer_path)
            print(f"Saved replay buffer: {replay_buffer_path}")
        return continue_training


def find_resume_replay_buffer(model_path):
    path = Path(model_path)
    stem = path.stem

    match = re.match(r"^(?P<prefix>.+)_(?P<steps>\d+)_steps$", stem)
    if match:
        candidate = path.with_name(
            f"{match.group('prefix')}_replay_buffer_{match.group('steps')}_steps.pkl"
        )
        if candidate.exists():
            return str(candidate)

    final_candidate = path.with_name(f"{stem}_replay_buffer.pkl")
    if final_candidate.exists():
        return str(final_candidate)

    replay_buffers = sorted(
        path.parent.glob("*_replay_buffer_*_steps.pkl"),
        key=lambda replay_path: replay_path.stat().st_mtime,
    )
    if replay_buffers:
        return str(replay_buffers[-1])

    return None


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--timesteps",      type=int,   default=2_000_000)
    p.add_argument("--n-envs",         type=int,   default=8)
    p.add_argument("--curriculum",     type=str,   default="easy_grasp",
                   choices=["none", "easy_grasp", "grasp_focus"])
    p.add_argument("--render",         action="store_true",
                   help="Render the first training environment in a MuJoCo viewer")
    p.add_argument("--resume",         type=str,   default=None,
                   help="Path to existing model zip to resume from")
    p.add_argument("--learning-rate",  type=float, default=3e-4)
    p.add_argument("--buffer-size",    type=int,   default=500_000)
    p.add_argument("--batch-size",     type=int,   default=512)
    return p.parse_args()


def make_env(curriculum, render_mode=None):
    def _init():
        return URGazeboSingleArmEnv(curriculum_mode=curriculum, render_mode=render_mode)
    return _init


def main():
    args  = parse_args()
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    run_name = f"gazebo_single_arm_{stamp}"

    log_dir   = os.path.join(LOG_ROOT, run_name)
    model_dir = os.path.join(MODEL_ROOT, run_name)
    os.makedirs(log_dir,   exist_ok=True)
    os.makedirs(model_dir, exist_ok=True)

    print(f"Run: {run_name}")
    print(f"Timesteps: {args.timesteps:,}  |  envs: {args.n_envs}  |  curriculum: {args.curriculum}")

    if args.render and args.n_envs != 1:
        raise ValueError("--render requires --n-envs 1 so a single MuJoCo viewer can be shown reliably.")

    train_env_fns = [
        make_env(args.curriculum, render_mode="human" if args.render and idx == 0 else None)
        for idx in range(args.n_envs)
    ]
    vec_env  = VecMonitor(DummyVecEnv(train_env_fns))
    eval_env = VecMonitor(DummyVecEnv([make_env(args.curriculum) for _ in range(4)]))

    eval_cb = EvalCallbackWithReplayBuffer(
        eval_env,
        best_model_save_path=model_dir,
        log_path=log_dir,
        eval_freq=max(20_000 // args.n_envs, 1),
        n_eval_episodes=20,
        deterministic=True,
        verbose=1,
    )
    ckpt_cb = CheckpointCallback(
        save_freq=max(100_000 // args.n_envs, 1),
        save_path=model_dir,
        name_prefix="ckpt",
        save_replay_buffer=True,
    )

    if args.resume:
        print(f"Resuming from {args.resume}")
        model = SAC.load(
            args.resume,
            env=vec_env,
            tensorboard_log=log_dir,
            learning_rate=args.learning_rate,
            buffer_size=args.buffer_size,
            batch_size=args.batch_size,
        )
        replay_buffer_path = find_resume_replay_buffer(args.resume)
        if replay_buffer_path:
            print(f"Loading replay buffer from {replay_buffer_path}")
            model.load_replay_buffer(replay_buffer_path)
        else:
            print("No replay buffer found for resume path; continuing with an empty replay buffer.")
    else:
        model = SAC(
            "MlpPolicy",
            vec_env,
            verbose=1,
            tensorboard_log=log_dir,
            learning_rate=args.learning_rate,
            buffer_size=args.buffer_size,
            batch_size=args.batch_size,
            gamma=0.99,
            tau=0.005,
            ent_coef=0.1,          # fixed entropy — prevents auto-tuning to zero
            learning_starts=50_000,
            train_freq=4,
            gradient_steps=2,
            policy_kwargs={"net_arch": [256, 256, 256]},
        )

    model.learn(
        total_timesteps=args.timesteps,
        callback=CallbackList([eval_cb, ckpt_cb]),
        progress_bar=True,
        reset_num_timesteps=args.resume is None,
    )

    final_path = os.path.join(model_dir, "final_model")
    model.save(final_path)
    final_replay_buffer_path = os.path.join(model_dir, "final_model_replay_buffer.pkl")
    model.save_replay_buffer(final_replay_buffer_path)
    print(f"Saved: {final_path}.zip")
    print(f"Saved replay buffer: {final_replay_buffer_path}")
    print(f"\nTo run in Gazebo:")
    print(f"  ros2 run mujoco_ur_rl_ros2 shared_arm_policy_node \\")
    print(f"    --ros-args -p model_path:={model_dir}/best_model.zip \\")
    print(f"    -p object_x:=0.35 -p object_y:=0.0 -p object_z:=0.045 \\")
    print(f"    -p drop_x:=0.35 -p drop_y:=0.20 -p drop_z:=0.025")


if __name__ == "__main__":
    main()
