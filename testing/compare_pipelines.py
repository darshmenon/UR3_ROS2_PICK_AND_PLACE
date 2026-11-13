#!/usr/bin/env python3
"""Side-by-side pick-and-place success: MotionExecutor results vs MTC results.

    python3 testing/compare_pipelines.py testing/benchmark_grippers_final3.csv testing/benchmark_mtc.csv
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402


def rates(path):
    out = defaultdict(lambda: [0, 0])
    for r in bench.load_rows(path):
        if not r["trial"]:
            continue
        out[(r["gripper"], r["object"])][1] += 1
        out[(r["gripper"], r["object"])][0] += r["success"]
    return out


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    ex, mtc = rates(sys.argv[1]), rates(sys.argv[2])
    keys = sorted(set(ex) | set(mtc), key=lambda k: (bench.DEFAULT_GRIPPERS.index(k[0])
                                                      if k[0] in bench.DEFAULT_GRIPPERS else 9, k[1]))

    def fmt(v):
        return "   -   " if not v or not v[1] else f"{v[0]}/{v[1]} {100 * v[0] / v[1]:>3.0f}%"

    print(f"{'gripper':<16}{'object':<14}{'MotionExecutor':>16}{'MTC':>14}")
    for k in keys:
        print(f"{k[0]:<16}{k[1]:<14}{fmt(ex.get(k)):>16}{fmt(mtc.get(k)):>14}")
    for name, d in (("MotionExecutor", ex), ("MTC", mtc)):
        ok = sum(v[0] for v in d.values())
        n = sum(v[1] for v in d.values())
        print(f"{name}: {ok}/{n} = {100 * ok / n:.0f}%" if n else f"{name}: no data")


if __name__ == "__main__":
    main()
