#!/usr/bin/env python3
"""Find the best tool0 -> fingertip offset per gripper by trying several in the sim.

Closing the fingers swings the pads along an arc relative to the flange (2F-140: ~17 mm lower at
5 cm width than when open), so the offset measured on the open gripper is not where the pads end up.
This runs benchmark_grippers.py once per candidate and prints passes per offset.

    python3 testing/sweep_tcp.py --gripper robotiq_2f_140 --offsets 0.192 0.200 0.209 0.218 \
        --objects cube_5cm cylinder_5cm --trials 3 --domain 91
"""
import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import benchmark_grippers as bench  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gripper", required=True, choices=bench.DEFAULT_GRIPPERS)
    ap.add_argument("--offsets", type=float, nargs="+", required=True)
    ap.add_argument("--objects", nargs="+", default=["cube_5cm", "cylinder_5cm"], choices=list(bench.OBJECTS))
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--out-dir", default="/tmp")
    args = ap.parse_args()

    results = {}
    for off in args.offsets:
        out = Path(args.out_dir) / f"sweep_{args.gripper}_{off:.3f}.csv"
        subprocess.run([sys.executable, str(HERE / "benchmark_grippers.py"), "--grippers", args.gripper,
                        "--objects", *args.objects, "--trials", str(args.trials), "--domain", str(args.domain),
                        "--settle", "45", "--tcp-offset", str(off), "--output", str(out)], check=False)
        rows = [r for r in bench.load_rows(out) if r["trial"]] if out.exists() else []
        results[off] = rows
    print(f"\nTCP offset sweep for {args.gripper}  ({args.trials} trials per object, pass = within 20 mm)")
    print(f"{'offset m':>9}  " + "  ".join(f"{o:>13}" for o in args.objects) + f"  {'total':>8}  {'mean err mm':>11}")
    best = None
    for off, rows in results.items():
        cells = []
        for o in args.objects:
            r = [x for x in rows if x["object"] == o]
            cells.append(f"{sum(x['success'] for x in r)}/{len(r)}")
        ok = sum(x["success"] for x in rows)
        errs = [x["error_xy_m"] * 1000 for x in rows if x["error_xy_m"] == x["error_xy_m"]]
        mean = sum(errs) / len(errs) if errs else float("nan")
        print(f"{off:>9.3f}  " + "  ".join(f"{c:>13}" for c in cells) + f"  {ok:>3}/{len(rows):<4}  {mean:>11.0f}")
        if best is None or ok > best[1]:
            best = (off, ok)
    if best:
        print(f"\nbest: {best[0]:.3f} ({best[1]} passes)")


if __name__ == "__main__":
    main()
