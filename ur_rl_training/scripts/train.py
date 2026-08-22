"""
Train a UR3 + Robotiq 2F-85 SAC pick-and-place policy.

Run from ur_rl_training/:
    python3 scripts/train.py [--curriculum grasp_focus] [--timesteps 3000000]

Best model and VecNormalize stats saved to models/checkpoints/<run>/.
Deploy with:
    ros2 launch ur_rl_training rl_policy.launch.py \
        model_path:=<path/to/best_model.zip>
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# The system triton package segfaults on import when torch builds an Adam
# optimizer (SAC._build). Block it before torch/stable_baselines3 load —
# CPU training here never needs triton kernels anyway. Same fix as
# ur_rl_training/policy_node.py.
sys.modules["triton"] = None

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from envs.ur3_pick_place_env import UR3PickPlaceEnv
from stable_baselines3 import SAC
from stable_baselines3.common.callbacks import (
    BaseCallback, CallbackList, CheckpointCallback, EvalCallback,
)
from stable_baselines3.common.save_util import load_from_zip_file
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor, VecNormalize

LOG_ROOT   = str(REPO_ROOT / "logs")
MODEL_ROOT = str(REPO_ROOT / "models" / "checkpoints")

CURRICULUM_ADVANCE_REWARD = 400.0


# ── callbacks ─────────────────────────────────────────────────────────────────

class NormEvalCallback(EvalCallback):
    """EvalCallback that keeps eval VecNormalize in sync and saves it alongside each best model."""

    def __init__(self, *args, train_env=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._train_env = train_env

    def _on_step(self) -> bool:
        if self._train_env is not None and hasattr(self.eval_env, "obs_rms"):
            self.eval_env.obs_rms = self._train_env.obs_rms
        prev_best = self.best_mean_reward
        result    = super()._on_step()
        if (self._train_env is not None
                and self.best_model_save_path is not None
                and self.best_mean_reward > prev_best):
            self._train_env.save(
                os.path.join(self.best_model_save_path, "vecnormalize.pkl"))
        return result


class PhaseMetricsCallback(BaseCallback):
    """Log peak-phase distribution and success rate to TensorBoard every eval_freq steps."""

    def __init__(self, eval_env, eval_freq, n_eval_episodes=20, verbose=0):
        super().__init__(verbose)
        self.eval_env        = eval_env
        self.eval_freq       = eval_freq
        self.n_eval_episodes = n_eval_episodes

    def _on_step(self) -> bool:
        if self.n_calls % self.eval_freq != 0:
            return True
        phase_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        successes    = 0
        ep           = 0
        peak_ph      = [0] * self.eval_env.num_envs
        obs          = self.eval_env.reset()
        while ep < self.n_eval_episodes:
            action, _ = self.model.predict(obs, deterministic=True)
            obs, _, dones, infos = self.eval_env.step(action)
            for i, (done, info) in enumerate(zip(dones, infos)):
                ph = info.get("phase", 0)
                if ph > peak_ph[i]:
                    peak_ph[i] = ph
                if done:
                    phase_counts[peak_ph[i]] = phase_counts.get(peak_ph[i], 0) + 1
                    if not info.get("TimeLimit.truncated", False):
                        successes += 1
                    peak_ph[i] = 0
                    ep += 1
                    if ep >= self.n_eval_episodes:
                        break
        total = self.n_eval_episodes
        for ph, label in [(0, "reach"), (1, "grasp"), (2, "lift"), (3, "place")]:
            self.logger.record(f"curriculum/phase_{label}", phase_counts.get(ph, 0) / total)
        self.logger.record("curriculum/success_rate", successes / total)
        return True


class CurriculumCallback(BaseCallback):
    """Advance from grasp_focus to full task once eval reward exceeds threshold."""

    def __init__(self, eval_cb, vec_env, threshold=CURRICULUM_ADVANCE_REWARD, verbose=1):
        super().__init__(verbose)
        self.eval_cb   = eval_cb
        self.vec_env   = vec_env
        self.threshold = threshold
        self._advanced = False

    def _on_step(self) -> bool:
        if self._advanced:
            return True
        if (self.eval_cb.last_mean_reward is not None
                and self.eval_cb.last_mean_reward >= self.threshold):
            if self.verbose:
                print(f"[Curriculum] advancing to full task "
                      f"(eval_reward={self.eval_cb.last_mean_reward:.1f})")
            self.vec_env.set_attr("curriculum_mode", "none")
            self._advanced = True
        return True


# ── helpers ───────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--timesteps",      type=int,   default=3_000_000)
    p.add_argument("--n-envs",         type=int,   default=8)
    p.add_argument("--curriculum",     type=str,   default="grasp_focus",
                   choices=["none", "grasp_focus"])
    p.add_argument("--resume",         type=str,   default=None,
                   help="Path to .zip checkpoint to resume")
    p.add_argument("--lr",             type=float, default=None,
                   help="Learning rate (default: 3e-4 fresh, 1e-4 when resuming)")
    p.add_argument("--ent-coef",       type=str,   default=None,
                   help="Entropy coef: 'auto' or float (default: auto fresh, 0.1 when resuming)")
    p.add_argument("--buffer-size",    type=int,   default=1_000_000)
    p.add_argument("--no-domain-rand", action="store_true",
                   help="Disable domain randomisation (for debugging)")
    return p.parse_args()


def make_env(curriculum, domain_rand):
    def _init():
        return UR3PickPlaceEnv(curriculum_mode=curriculum, domain_randomisation=domain_rand)
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

    inner_vec  = VecMonitor(DummyVecEnv([make_env(args.curriculum, dom)] * args.n_envs))
    inner_eval = VecMonitor(DummyVecEnv([make_env(args.curriculum, False)] * 4))

    norm_path = Path(args.resume).parent / "vecnormalize.pkl" if args.resume else None
    if norm_path and norm_path.exists():
        vec_env  = VecNormalize.load(str(norm_path), inner_vec)
        eval_env = VecNormalize.load(str(norm_path), inner_eval)
        eval_env.training    = False
        eval_env.norm_reward = False
        print(f"VecNormalize loaded from {norm_path}")
    else:
        vec_env  = VecNormalize(inner_vec,  norm_obs=True, norm_reward=True,  clip_obs=10.0)
        eval_env = VecNormalize(inner_eval, norm_obs=True, norm_reward=False,
                                clip_obs=10.0, training=False)

    eval_freq = max(20_000 // args.n_envs, 1)
    eval_cb = NormEvalCallback(
        eval_env,
        train_env=vec_env,
        best_model_save_path=mdl_dir,
        log_path=log_dir,
        eval_freq=eval_freq,
        n_eval_episodes=20,
        deterministic=True,
        verbose=1,
    )
    phase_cb      = PhaseMetricsCallback(eval_env, eval_freq=eval_freq, n_eval_episodes=20)
    curriculum_cb = CurriculumCallback(eval_cb, vec_env)
    ckpt_cb       = CheckpointCallback(
        save_freq=max(100_000 // args.n_envs, 1),
        save_path=mdl_dir,
        name_prefix="ckpt",
    )

    if args.resume:
        print(f"Resuming from {args.resume}")
        _, params, _ = load_from_zip_file(args.resume, device="auto")
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
            learning_starts=0,
            train_freq=4,
            gradient_steps=4,
            policy_kwargs={"net_arch": [256, 256, 256]},
        )
        model.set_parameters({"policy": params["policy"]}, exact_match=False)
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
        callback=CallbackList([eval_cb, phase_cb, curriculum_cb, ckpt_cb]),
        progress_bar=True,
        reset_num_timesteps=args.resume is None,
    )

    final = os.path.join(mdl_dir, "final_model")
    model.save(final)
    vec_env.save(os.path.join(mdl_dir, "vecnormalize.pkl"))
    print(f"\nSaved: {final}.zip")
    print(f"\nDeploy in Gazebo:")
    print(f"  ros2 launch ur_rl_training rl_policy.launch.py \\")
    print(f"    model_path:={mdl_dir}/best_model.zip")


if __name__ == "__main__":
    main()
