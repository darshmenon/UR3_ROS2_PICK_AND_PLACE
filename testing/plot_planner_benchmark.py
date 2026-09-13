#!/usr/bin/env python3
"""Plot a planner comparison (success rate + planning time) from a
benchmark_planners.py CSV.

Usage:
    python3 testing/plot_planner_benchmark.py logs/planner_benchmark_20260913_120000.csv
    python3 testing/plot_planner_benchmark.py   # uses the newest logs/planner_benchmark_*.csv
"""
import csv
import glob
import os
import sys
from collections import defaultdict

import matplotlib.pyplot as plt

LOGS_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
OUT = os.path.join(os.path.dirname(__file__), "planner_benchmark_bar.png")


def find_csv():
    if len(sys.argv) > 1:
        return sys.argv[1]
    candidates = sorted(glob.glob(os.path.join(LOGS_DIR, "planner_benchmark_*.csv")))
    if not candidates:
        raise SystemExit("no logs/planner_benchmark_*.csv found — run testing/benchmark_planners.py first")
    return candidates[-1]


def load(path):
    by_case = defaultdict(list)
    with open(path) as f:
        for row in csv.DictReader(f):
            by_case[row["case"]].append(row)
    return by_case


def main():
    path = find_csv()
    print(f"reading {path}")
    by_case = load(path)

    cases = sorted(by_case)
    success_rate, avg_time, min_time, max_time = [], [], [], []
    for c in cases:
        rows = by_case[c]
        n = len(rows)
        successes = sum(r["success"].lower() == "true" for r in rows)
        times = [float(r["planning_time_s"]) for r in rows]
        success_rate.append(successes / n * 100)
        avg_time.append(sum(times) / n)
        min_time.append(min(times))
        max_time.append(max(times))

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].bar(cases, success_rate, color="#4C72B0")
    axes[0].set_ylabel("Success rate (%)")
    axes[0].set_title("Success rate by case")
    axes[0].set_ylim(0, 100)
    axes[0].tick_params(axis="x", rotation=30)
    axes[0].grid(alpha=0.3, axis="y")
    for i, v in enumerate(success_rate):
        axes[0].text(i, v + 2, f"{v:.0f}%", ha="center")

    err = [
        [a - mn for a, mn in zip(avg_time, min_time)],
        [mx - a for a, mx in zip(avg_time, max_time)],
    ]
    axes[1].bar(cases, avg_time, yerr=err, capsize=4, color="#DD8452")
    axes[1].set_ylabel("Planning time (s)")
    axes[1].set_title("Planning time by case (mean, min–max)")
    axes[1].tick_params(axis="x", rotation=30)
    axes[1].grid(alpha=0.3, axis="y")

    fig.suptitle(os.path.basename(path))
    fig.tight_layout()
    fig.savefig(OUT, dpi=150)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
