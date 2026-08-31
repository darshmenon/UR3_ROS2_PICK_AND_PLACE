#!/usr/bin/env python3
"""Compare SAC training runs using their evaluations.npz logs.

Usage:
    python3 testing/plot_rl_run_comparison.py
"""
import glob
import os

import matplotlib.pyplot as plt
import numpy as np

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "ur_rl_training", "logs")
OUT_DIR = os.path.dirname(__file__)


def load_runs():
    runs = []
    for path in sorted(glob.glob(os.path.join(LOGS_DIR, "*", "evaluations.npz"))):
        name = os.path.basename(os.path.dirname(path))
        data = np.load(path)
        runs.append({
            "name": name,
            "timesteps": data["timesteps"],
            "mean_reward": data["results"].mean(axis=1),
        })
    return runs


def plot_learning_curves(runs):
    fig, ax = plt.subplots(figsize=(10, 6))
    for run in runs:
        ax.plot(run["timesteps"], run["mean_reward"], label=run["name"], alpha=0.8)
    ax.set_xlabel("Training timesteps")
    ax.set_ylabel("Mean eval reward")
    ax.set_title("SAC pick-place training runs")
    ax.legend(fontsize=7, loc="upper left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = os.path.join(OUT_DIR, "rl_learning_curves.png")
    fig.savefig(out, dpi=150)
    print(f"saved {out}")


def plot_best_reward_bar(runs):
    names = [r["name"] for r in runs]
    best = [r["mean_reward"].max() for r in runs]
    order = np.argsort(best)
    names = [names[i] for i in order]
    best = [best[i] for i in order]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, best, color="#4C72B0")
    ax.set_xlabel("Best mean eval reward")
    ax.set_title("Best reward reached per training run")
    ax.bar_label(bars, fmt="%.0f", padding=3, fontsize=8)
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout()
    out = os.path.join(OUT_DIR, "rl_best_reward_bar.png")
    fig.savefig(out, dpi=150)
    print(f"saved {out}")


if __name__ == "__main__":
    runs = load_runs()
    if not runs:
        raise SystemExit(f"no evaluations.npz found under {LOGS_DIR}")
    plot_learning_curves(runs)
    plot_best_reward_bar(runs)
