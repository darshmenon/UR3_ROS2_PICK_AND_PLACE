#!/usr/bin/env python3
"""Summarize Gazebo single-arm training runs from saved eval and checkpoint artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np


DEFAULT_LOG_ROOT = Path("logs/gazebo_single_arm")
DEFAULT_MODEL_ROOT = Path("models/gazebo_single_arm")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "runs",
        nargs="*",
        help="Optional run names such as gazebo_single_arm_20260418_0928.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="How many recent runs to show when no run names are provided.",
    )
    return parser.parse_args()


def load_eval_summary(run_name: str) -> dict[str, object]:
    eval_path = DEFAULT_LOG_ROOT / run_name / "evaluations.npz"
    model_dir = DEFAULT_MODEL_ROOT / run_name
    summary: dict[str, object] = {
        "run": run_name,
        "eval_path": eval_path,
        "model_dir": model_dir,
        "status": "ok",
        "best_checkpoint": model_dir / "best_model.zip",
    }

    if not eval_path.exists():
        summary["status"] = "missing evaluations.npz"
        return summary

    data = np.load(eval_path)
    timesteps = np.asarray(data["timesteps"]).reshape(-1)
    results = np.asarray(data["results"])
    mean_rewards = results.mean(axis=1)
    std_rewards = results.std(axis=1)
    best_idx = int(mean_rewards.argmax())
    last_idx = len(mean_rewards) - 1

    summary.update(
        {
            "best_timestep": int(timesteps[best_idx]),
            "best_mean_reward": float(mean_rewards[best_idx]),
            "best_reward_std": float(std_rewards[best_idx]),
            "last_timestep": int(timesteps[last_idx]),
            "last_mean_reward": float(mean_rewards[last_idx]),
            "num_evals": int(len(mean_rewards)),
        }
    )
    return summary


def recent_run_names(limit: int) -> list[str]:
    if not DEFAULT_LOG_ROOT.exists():
        return []
    run_dirs = [path for path in DEFAULT_LOG_ROOT.iterdir() if path.is_dir()]
    run_dirs.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [path.name for path in run_dirs[:limit]]


def format_summary(summary: dict[str, object]) -> str:
    if summary["status"] != "ok":
        return f"{summary['run']}: {summary['status']}"

    best_model = summary["best_checkpoint"]
    best_exists = "yes" if Path(best_model).exists() else "no"
    return (
        f"{summary['run']}: "
        f"best {summary['best_mean_reward']:.2f} @ {summary['best_timestep']:,} | "
        f"last {summary['last_mean_reward']:.2f} @ {summary['last_timestep']:,} | "
        f"evals {summary['num_evals']} | "
        f"best_model {best_exists}"
    )


def main() -> None:
    args = parse_args()
    run_names = args.runs or recent_run_names(args.limit)
    if not run_names:
        print("No runs found under logs/gazebo_single_arm.")
        return

    for run_name in run_names:
        print(format_summary(load_eval_summary(run_name)))


if __name__ == "__main__":
    main()
