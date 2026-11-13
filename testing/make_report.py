#!/usr/bin/env python3
"""Write a markdown results report from benchmark CSVs.

    python3 testing/make_report.py --executor testing/benchmark_grippers_final3.csv \
        [--mtc testing/benchmark_mtc.csv] [--out testing/RESULTS.md] [--title "..."]

pick = the object rose at least 3 cm (or, in older CSVs, left its start spot);
place = ended within tolerance of the target (of the picked trials);
pick & place = both, the overall success rate. Every number comes from the object's true
position in Gazebo, not from what the robot reports.
"""
import argparse
import math
import statistics
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402


def pct(n, d):
    return "-" if not d else f"{100 * n / d:.0f}%"


def cell_stats(rows):
    picked = [r for r in rows if bench._picked(r)]
    ok = [r for r in rows if r["success"]]
    errs = [r["error_xy_m"] * 1000 for r in rows if not math.isnan(r["error_xy_m"])]
    best = [r["error_xy_m"] * 1000 for r in ok]
    return dict(n=len(rows), pick=pct(len(picked), len(rows)), place=pct(len(ok), len(picked)),
                pp=pct(len(ok), len(rows)), passes=len(ok),
                err=f"{statistics.mean(best):.0f}" if best else "-",
                cyc=f"{statistics.mean(r['cycle_time_s'] for r in rows):.0f}" if rows else "-")


def table(rows, grippers, objects):
    lines = ["| gripper | object | trials | pick | place | pick & place | mean error of passes (mm) | cycle (s) |",
             "|---|---|---|---|---|---|---|---|"]
    for g in grippers:
        for o in objects:
            r = [x for x in rows if x["gripper"] == g and x["object"] == o]
            if r:
                s = cell_stats(r)
                lines.append(f"| {g} | {o} | {s['n']} | {s['pick']} | {s['place']} | {s['pp']} "
                             f"({s['passes']}/{s['n']}) | {s['err']} | {s['cyc']} |")
    return lines


def overall(rows, grippers):
    lines = ["| gripper | trials | pick | place | pick & place |", "|---|---|---|---|---|"]
    for g in grippers:
        r = [x for x in rows if x["gripper"] == g]
        if r:
            s = cell_stats(r)
            lines.append(f"| {g} | {s['n']} | {s['pick']} | {s['place']} | {s['pp']} ({s['passes']}/{s['n']}) |")
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--executor", required=True, help="benchmark_grippers.py CSV (MotionExecutor)")
    ap.add_argument("--mtc", default=None, help="benchmark_mtc.py CSV")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "RESULTS.md"))
    ap.add_argument("--title", default="UR3 gripper pick-and-place benchmark")
    args = ap.parse_args()

    ex = [r for r in bench.load_rows(args.executor) if r["trial"]]
    grippers = [g for g in bench.DEFAULT_GRIPPERS if any(r["gripper"] == g for r in ex)]
    objects = [o for o in bench.OBJECTS if any(r["object"] == o for r in ex)]
    L = [f"# {args.title}", "", f"Generated {date.today()} from `{Path(args.executor).name}`"
         + (f" and `{Path(args.mtc).name}`" if args.mtc else "") + ".", "",
         "## How it is measured", "",
         "- Task: pick the object at (0.35, 0.00) and place it at (0.35, 0.20) in the robot base frame, in Gazebo.",
         "- Truth: the object's real position read from Gazebo before and after every trial, not the robot's own report.",
         "- **pick**: the object rose at least 3 cm (older runs: it left its start spot, which also counts a dragged object).",
         "- **place**: of the picked trials, the object ended within 20 mm of the target.",
         "- **pick & place**: both, i.e. the overall success rate.", "",
         "## MotionExecutor (IK + Pilz point-to-point)", "", "### Per gripper", ""] + overall(ex, grippers)
    L += ["", "### Per gripper and object", ""] + table(ex, grippers, objects)
    if args.mtc:
        mtc = [r for r in bench.load_rows(args.mtc) if r["trial"]]
        L += ["", "## MoveIt Task Constructor (MTC)", "", "### Per gripper", ""] + overall(
            mtc, [g for g in bench.DEFAULT_GRIPPERS if any(r["gripper"] == g for r in mtc)])
        L += ["", "### Per gripper and object", ""] + table(
            mtc, grippers, [o for o in bench.OBJECTS if any(r["object"] == o for r in mtc)])
        L += ["", "### Same cells, side by side (pick & place passes)", "",
              "| gripper | object | MotionExecutor | MTC |", "|---|---|---|---|"]
        for g in grippers:
            for o in objects:
                a = [r for r in ex if r["gripper"] == g and r["object"] == o]
                b = [r for r in mtc if r["gripper"] == g and r["object"] == o]
                if a and b:
                    L.append(f"| {g} | {o} | {sum(r['success'] for r in a)}/{len(a)} | "
                             f"{sum(r['success'] for r in b)}/{len(b)} |")
    L += ["", "## Notes", "", "- Fill in findings and caveats here after reading the per-trial CSV.", ""]
    Path(args.out).write_text("\n".join(L))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
