#!/usr/bin/env python3
"""Does the benchmark cylinder stay put on the table? Standalone sim (world only, no robot, no ROS), own gz partition.

    python3 testing/cylinder_stability.py --resets 6 --watch 25 --variants base phys_inertia ...

For each model variant it starts the world headless with the same physics engine as the real launch, resets the cylinder
upright (like benchmark_mtc.py) and watches its true pose. A reset "holds" if z stays within 4 mm and xy within 5 mm of the
start for the whole watch time. The benchmark loses trials to a cylinder that rocks, creeps and tips after a reset or a
release, so this is the quick (about 3 minutes per variant) way to try model changes before a 12 minute MTC run.
"""
import argparse
import math
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402

SRC = bench.REPO / "ur_gazebo" / "worlds" / "colored_cylinder.world"
ENGINE = "gz-physics-bullet-featherstone-plugin"
# name -> list of (regex, replacement) applied to the world text
PHYS_I = ("<ixx>0.0002</ixx><ixy>0</ixy><ixz>0</ixz>\\s*<iyy>0.0002</iyy><iyz>0</iyz>\\s*<izz>0.0002</izz>",
          "<ixx>6.9e-5</ixx><ixy>0</ixy><ixz>0</ixz><iyy>6.9e-5</iyy><iyz>0</iyz><izz>3.1e-5</izz>")
VARIANTS = {
    "base": [],
    "phys_inertia": [PHYS_I],
    "mu1_phys": [PHYS_I, ("<mu>1.5</mu><mu2>1.5</mu2>", "<mu>1.0</mu><mu2>1.0</mu2>")],
    "heavy_phys": [PHYS_I, ("<mass>0.1</mass>", "<mass>0.2</mass>"),
                   ("<ixx>6.9e-5</ixx>", "<ixx>1.4e-4</ixx>"), ("<iyy>6.9e-5</iyy>", "<iyy>1.4e-4</iyy>"),
                   ("<izz>3.1e-5</izz>", "<izz>6.2e-5</izz>")],
}


def make_world(variant, out_dir):
    text = SRC.read_text()
    for pat, rep in VARIANTS[variant]:
        new, n = re.subn(pat, rep, text)
        if n != 1:
            raise SystemExit(f"variant {variant}: pattern {pat!r} matched {n} times")
        text = new
    path = out_dir / f"cyl_{variant}.world"
    path.write_text(text)
    return path


def measure(variant, resets, watch, lift, wait=90):
    holds, rows = 0, []
    start = time.time()
    initial = None
    while time.time() - start < wait and initial is None:
        time.sleep(2)
        initial = bench.object_pose()
    if initial is None:
        return None
    last = None
    for _ in range(30):                       # resting reference once z stops changing
        time.sleep(1)
        initial = bench.object_pose()
        if initial and last and max(abs(a - b) for a, b in zip(initial, last)) < 5e-4:
            break
        last = initial
    for r in range(resets):
        bench.reset_object(initial, lift=lift)
        t0, worst_z, worst_xy = time.time(), 0.0, 0.0
        while time.time() - t0 < watch:
            p = bench.object_pose()
            if p:
                worst_z = max(worst_z, abs(p[2] - initial[2]))
                worst_xy = max(worst_xy, math.hypot(p[0] - initial[0], p[1] - initial[1]))
            time.sleep(0.5)
        ok = worst_z < 0.004 and worst_xy < 0.005
        holds += ok
        rows.append((r + 1, ok, worst_z * 1000, worst_xy * 1000))
        print(f"[{variant}] reset {r + 1}: {'HOLDS' if ok else 'moves'}  max dz={worst_z * 1000:.1f} mm  "
              f"max dxy={worst_xy * 1000:.1f} mm", flush=True)
    return holds, rows


def run_robot(gripper, resets, watch, lift):
    """Same measurement inside the real launch (UR3 + controllers running, arm holding still at its start pose)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import benchmark_mtc as mtc
    os.environ["ROS_DOMAIN_ID"] = "91"
    sim = bench.launch_sim(gripper, "colored_cylinder.world", 91, 45)
    try:
        mtc.wait_controllers(91, timeout=300.0)
        return measure("with_robot", resets, watch, lift)
    finally:
        bench.stop_sim(sim)


def run_variant(variant, world, resets, watch, lift):
    models = str(bench.REPO / "ur_gazebo" / "models")      # the launch file normally sets this (mount_table etc.)
    env = dict(os.environ, GZ_PARTITION="cylstab", GZ_VERSION="harmonic",
               GZ_SIM_RESOURCE_PATH=models + (":" + os.environ["GZ_SIM_RESOURCE_PATH"]
                                              if os.environ.get("GZ_SIM_RESOURCE_PATH") else ""))
    os.environ.update(GZ_PARTITION="cylstab")
    proc = subprocess.Popen(["gz", "sim", "-s", "-r", "-v", "2", "--headless-rendering", "--physics-engine", ENGINE,
                             str(world)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            preexec_fn=os.setsid)
    try:
        return measure(variant, resets, watch, lift)
    finally:
        for sig in (signal.SIGINT, signal.SIGKILL):
            try:
                os.killpg(os.getpgid(proc.pid), sig)
                proc.wait(timeout=15)
                break
            except (subprocess.TimeoutExpired, ProcessLookupError):
                continue
    return holds, rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS), choices=list(VARIANTS))
    ap.add_argument("--resets", type=int, default=6)
    ap.add_argument("--watch", type=float, default=25.0)
    ap.add_argument("--lift", type=float, default=0.0, help="reset height above the resting pose (a release drop)")
    ap.add_argument("--robot", action="store_true", help="measure inside the full UR3 launch instead of a bare world")
    ap.add_argument("--gripper", default="robotiq_2f_140")
    ap.add_argument("--out-dir", default=str(bench.REPO / "testing" / "_out" / "cyl_worlds"))
    args = ap.parse_args()
    bench.OBJECT = "red_cylinder"
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if args.robot:
        res = run_robot(args.gripper, args.resets, args.watch, args.lift)
        print(f"\nwith_robot holds: {res[0] if res else 'sim failed'}/{args.resets}")
        return
    summary = {}
    for v in args.variants:
        res = run_variant(v, make_world(v, out), args.resets, args.watch, args.lift)
        summary[v] = res[0] if res else None
    print("\nvariant         holds")
    for v, h in summary.items():
        print(f"{v:15s} {'sim failed' if h is None else f'{h}/{args.resets}'}")


if __name__ == "__main__":
    main()
