"""
Train a UR3 + Robotiq 2F-85 SAC pick-and-place policy.

Run from ur_rl_training/:
    python3 scripts/train.py [--curriculum grasp_focus] [--timesteps 2000000]

Best model saved to models/checkpoints/<run>/best_model.zip
Deploy with:
    ros2 launch ur_rl_training rl_policy.launch.py \
        model_path:=<path/to/best_model.zip>
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from envs.ur3_pick_place_env import UR3PickPlaceEnv
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback, EvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

LOG_ROOT   = str(REPO_ROOT / "logs")
MODEL_ROOT = str(REPO_ROOT / "models" / "checkpoints")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--timesteps",    type=int,   default=3_000_000)
    p.add_argument("--n-envs",       type=int,   default=8)
    p.add_argument("--curriculum",   type=str,   default="grasp_focus",
                   choices=["none", "grasp_focus"])
    p.add_argument("--resume",       type=str,   default=None,
                   help="Path to .zip checkpoint to resume")
    p.add_argument("--lr",           type=float, default=None,
                   help="Learning rate (default: 3e-4 fresh, 1e-4 when resuming)")
    p.add_argument("--ent-coef",     type=str,   default=None,
                   help="Entropy coef: 'auto' or float (default: auto fresh, 0.1 when resuming)")
    p.add_argument("--buffer-size",  type=int,   default=1_000_000)
    p.add_argument("--no-domain-rand", action="store_true",
                   help="Disable domain randomisation (for debugging)")
    return p.parse_args()


def make_env(curriculum, domain_rand):
    def _init():
        return UR3PickPlaceEnv(curriculum_mode=curriculum,
                               domain_randomisation=domain_rand)
    return _init


def main():
    args     = parse_args()
    stamp    = datetime.now().strftime("%Y%m%d_%H%M")
    run_name = f"ur3_pick_place_{stamp}"
    log_dir  = os.path.join(LOG_ROOT, run_name)
    mdl_dir  = os.path.join(MODEL_ROOT, run_name)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(mdl_dir, exist_ok=True)

    dom = not args.no_domain_rand
    lr  = args.lr if args.lr is not None else (1e-4 if args.resume else 3e-4)
    ent = args.ent_coef if args.ent_coef is not None else (0.1 if args.resume else "auto")
    if ent != "auto":
        try: ent = float(ent)
        except ValueError: ent = "auto"
    print(f"Run: {run_name}")
    print(f"Steps: {args.timesteps:,}  envs: {args.n_envs}  lr: {lr}  ent_coef: {ent}  "
          f"curriculum: {args.curriculum}  domain_rand: {dom}")

    vec_env  = VecMonitor(DummyVecEnv([make_env(args.curriculum, dom)] * args.n_envs))
    eval_env = VecMonitor(DummyVecEnv([make_env(args.curriculum, False)] * 4))

    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path=mdl_dir,
        log_path=log_dir,
        eval_freq=max(20_000 // args.n_envs, 1),
        n_eval_episodes=20,
        deterministic=True,
        verbose=1,
    )
    ckpt_cb = CheckpointCallback(
        save_freq=max(100_000 // args.n_envs, 1),
        save_path=mdl_dir,
        name_prefix="ckpt",
    )

    if args.resume:
        print(f"Resuming from {args.resume}")
        model = SAC.load(args.resume, env=vec_env,
                         custom_objects={"learning_rate": lr,
                                         "n_steps": args.buffer_size})
        model.learning_rate = lr
        model.ent_coef = ent
    else:
        model = SAC(
            "MlpPolicy", vec_env,
            verbose=1,
            tensorboard_log=log_dir,
            learning_rate=lr,
            buffer_size=args.buffer_size,
            batch_size=512,
            gamma=0.99,
            tau=0.005,
            ent_coef=ent,
            learning_starts=10_000,
            train_freq=4,
            gradient_steps=4,
            policy_kwargs={"net_arch": [256, 256, 256]},
        )

    model.learn(
        total_timesteps=args.timesteps,
        callback=CallbackList([eval_cb, ckpt_cb]),
        progress_bar=True,
        reset_num_timesteps=args.resume is None,
    )

    final = os.path.join(mdl_dir, "final_model")
    model.save(final)
    print(f"\nSaved: {final}.zip")
    print(f"\nDeploy in Gazebo:")
    print(f"  ros2 launch ur_rl_training rl_policy.launch.py \\")
    print(f"    model_path:={mdl_dir}/best_model.zip")


if __name__ == "__main__":
    main()
