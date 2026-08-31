#!/usr/bin/env python3
"""Plot a policy comparison (success rate + cycle time) from a benchmark_policies.py CSV.

Usage:
    python3 testing/plot_benchmark_comparison.py logs/benchmark_20260825_120000.csv
    python3 testing/plot_benchmark_comparison.py   # uses the newest logs/benchmark_*.csv
"""
import csv
import glob
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
OUT = os.path.join(os.path.dirname(__file__), "benchmark_comparison_bar.png")


def find_csv():
    if len(sys.argv) > 1:
        return sys.argv[1]
    candidates = sorted(glob.glob(os.path.join(LOGS_DIR, "benchmark_*.csv")))
    if not candidates:
        raise SystemExit(f"no logs/benchmark_*.csv found — run testing/benchmark_policies.py first")
    return candidates[-1]


def load(path):
    by_policy = defaultdict(list)
    with open(path) as f:
        for row in csv.DictReader(f):
            by_policy[row["policy"]].append(row)
    return by_policy


def main():
    path = find_csv()
    print(f"reading {path}")
    by_policy = load(path)

    policies = sorted(by_policy)
    success_rate = []
    avg_time = []
    for p in policies:
        rows = by_policy[p]
        n = len(rows)
        successes = sum(r["success"].lower() == "true" for r in rows)
        success_rate.append(successes / n * 100)
        avg_time.append(sum(float(r["cycle_time_s"]) for r in rows) / n)

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))

    axes[0].bar(policies, success_rate, color="#4C72B0")
    axes[0].set_ylabel("Success rate (%)")
    axes[0].set_title("Success rate by policy")
    axes[0].set_ylim(0, 100)
    axes[0].grid(alpha=0.3, axis="y")
    for i, v in enumerate(success_rate):
        axes[0].text(i, v + 2, f"{v:.0f}%", ha="center")

    axes[1].bar(policies, avg_time, color="#DD8452")
    axes[1].set_ylabel("Avg cycle time (s)")
    axes[1].set_title("Cycle time by policy")
    axes[1].grid(alpha=0.3, axis="y")
    for i, v in enumerate(avg_time):
        axes[1].text(i, v + 0.5, f"{v:.1f}s", ha="center")

    fig.suptitle(os.path.basename(path))
    fig.tight_layout()
    fig.savefig(OUT, dpi=150)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
