#!/usr/bin/env python3
"""Pick-and-place benchmark through MoveIt Task Constructor (MTC), scored like benchmark_grippers.py.

Same grippers, objects, worlds, ground-truth scoring (true object pose from Gazebo, within --tol of
pick + (0, 0.20)), so the CSV can be put next to the MotionExecutor results:

    python3 testing/benchmark_mtc.py --grippers robotiq_2f_85 --objects cube_5cm --trials 3 --domain 91 \
        --output testing/benchmark_mtc.csv
    python3 testing/compare_pipelines.py testing/benchmark_grippers_final3.csv testing/benchmark_mtc.csv

Each trial resets the object, asks the MTC retry node (ur_bt_planner mtc_retry.launch.py) for ONE
attempt (--attempts) and waits for its SUCCESS/FAILURE status. MTC does its own perception and
grasp search, so there is no pick position to pass in. One cell per process, one sim at a time.
"""
import argparse
import csv
import math
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402

FIELDS = ["pipeline", "gripper", "object", "trial", "executed", "success", "error_xy_m", "error_z_m",
          "perception_error_xy_m", "cycle_time_s", "lifted_m", "err_dx_m", "err_dy_m", "notes"]


def launch_mtc(gripper, domain, attempts, startup):
    env = dict(os.environ, ROS_DOMAIN_ID=str(domain), GZ_VERSION="harmonic")
    cmd = ["bash", "-c",
           f"source /opt/ros/humble/setup.bash && source {bench.REPO}/install/setup.bash && "
           f"exec ros2 launch ur_bt_planner mtc_retry.launch.py gripper:={gripper} max_attempts:={attempts}"]
    log = open(bench.REPO / "logs" / f"bench_mtc_{gripper}.log", "w")
    proc = subprocess.Popen(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, preexec_fn=os.setsid)
    time.sleep(startup)
    return proc


def run_cell(args, g, name):
    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    import rclpy
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from std_msgs.msg import String
    from std_srvs.srv import Trigger

    obj = bench.OBJECTS[name]
    bench.OBJECT = obj["model"]
    bench.OBJECT_YAW = 0.0
    (bench.REPO / "logs").mkdir(exist_ok=True)
    rows = []
    rclpy.init()
    sim = bench.launch_sim(g, obj["world"], args.domain, args.settle)
    mtc = launch_mtc(g, args.domain, args.attempts, args.mtc_startup)
    node = Node("benchmark_mtc")
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    threading.Thread(target=executor.spin, daemon=True).start()
    status = {"text": ""}
    node.create_subscription(String, "/mtc_bt/status", lambda m: status.update(text=m.data), 10)
    client = node.create_client(Trigger, "/mtc_bt/run")
    try:
        if not client.wait_for_service(timeout_sec=90.0):
            rows.append(dict(pipeline="mtc", gripper=g, object=name, trial=0, executed=False, success=False,
                             error_xy_m=float("nan"), error_z_m=float("nan"),
                             perception_error_xy_m=float("nan"), cycle_time_s=0.0,
                             lifted_m=float("nan"), err_dx_m=float("nan"), err_dy_m=float("nan"),
                             notes="mtc not ready"))
            return rows
        initial = bench.object_pose()
        for t in range(1, args.trials + 1):
            before = bench.object_pose()
            status["text"] = ""
            t0 = time.time()
            with bench.LiftWatcher() as watcher:
                resp = None
                fut = client.call_async(Trigger.Request())
                end = time.time() + 20
                while not fut.done() and time.time() < end:
                    time.sleep(0.1)
                resp = fut.result() if fut.done() else None
                notes = ""
                if resp is None or not resp.success:
                    notes = f"run not accepted: {getattr(resp, 'message', 'no reply')}"
                else:
                    end = time.time() + args.trial_timeout
                    while time.time() < end and not any(k in status["text"] for k in ("SUCCESS", "FAILURE", "stopped")):
                        time.sleep(1.0)
                    if not any(k in status["text"] for k in ("SUCCESS", "FAILURE", "stopped")):
                        notes = "timeout"
            cycle = time.time() - t0
            time.sleep(2.0)   # let the object settle
            after = bench.object_pose()
            ex_xy = ex_z = err_dx = err_dy = float("nan")
            success = False
            if before is None or after is None:
                notes = (notes + "; " if notes else "") + "no gz pose"
            else:
                tx = before[0] + (bench.PLACE_XY[0] - bench.PICK_XY[0])
                ty = before[1] + (bench.PLACE_XY[1] - bench.PICK_XY[1])
                err_dx, err_dy = after[0] - tx, after[1] - ty
                ex_xy = math.hypot(err_dx, err_dy)
                ex_z = after[2] - before[2]
                moved = math.hypot(after[0] - before[0], after[1] - before[1]) > 0.05
                success = moved and ex_xy < args.tol
                if not moved:
                    notes = (notes + "; " if notes else "") + "object not moved"
            lifted = (watcher.max_z - before[2]) if (before is not None and watcher.max_z is not None) \
                else float("nan")
            rows.append(dict(pipeline="mtc", gripper=g, object=name, trial=t,
                             executed="SUCCESS" in status["text"], success=success, error_xy_m=ex_xy,
                             error_z_m=ex_z, perception_error_xy_m=float("nan"), cycle_time_s=cycle,
                             lifted_m=lifted, err_dx_m=err_dx, err_dy_m=err_dy, notes=(notes + " | " if notes else "") + status["text"]))
            print(f"[mtc] {g}/{name} trial {t}: success={success} xy={ex_xy * 1000:.0f}mm "
                  f"status={status['text']!r} {cycle:.0f}s", flush=True)
            bench.reset_object(initial)
    finally:
        for p in (mtc,):
            try:
                os.killpg(os.getpgid(p.pid), signal.SIGINT)
                p.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(p.pid), signal.SIGKILL)   # only our own launch's process group
            except ProcessLookupError:
                pass
        bench.stop_sim(sim)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--grippers", nargs="+", default=bench.DEFAULT_GRIPPERS)
    ap.add_argument("--objects", nargs="+", default=list(bench.OBJECTS), choices=list(bench.OBJECTS))
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--attempts", type=int, default=1, help="MTC attempts per trial (1 = no retries)")
    ap.add_argument("--tol", type=float, default=0.02)
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--settle", type=float, default=45.0, help="seconds after the sim launch")
    ap.add_argument("--mtc-startup", type=float, default=40.0, help="seconds after the MTC launch")
    ap.add_argument("--trial-timeout", type=float, default=420.0)
    ap.add_argument("--output", default=None)
    ap.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    out = Path(args.output or bench.REPO / "testing" / f"benchmark_mtc_{datetime.now():%Y%m%d_%H%M%S}.csv")
    if args.child:
        rows = run_cell(args, args.grippers[0], args.objects[0])
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        return 0

    all_rows = []
    for g in args.grippers:
        for name in args.objects:
            tmp = out.with_suffix(f".{g}.{name}.tmp.csv")
            subprocess.run([sys.executable, str(Path(__file__).resolve()), "--child", "--grippers", g,
                            "--objects", name, "--trials", str(args.trials), "--attempts", str(args.attempts),
                            "--tol", str(args.tol), "--domain", str(args.domain), "--settle", str(args.settle),
                            "--mtc-startup", str(args.mtc_startup), "--trial-timeout", str(args.trial_timeout),
                            "--output", str(tmp)], check=False)
            if tmp.exists():
                all_rows += bench.load_rows_from(list(csv.DictReader(open(tmp))))
                tmp.unlink()
    if not all_rows:
        print("no results")
        return 1
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    bench.summarise([r for r in all_rows if r["trial"]], args.grippers, args.objects)
    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
