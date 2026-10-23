#!/usr/bin/env python3
"""Collect labelled grasp data in the sim for training grasp models.

Each trial: put the object at a random spot and rotation, look at it from the scan pose,
try a grasp at a random offset from the true pose, close, lift 15 cm, and record whether it
really came up (true height from Gazebo). Saved per trial:

  <out>/frames/NNNNN_scan.jpg    wrist camera at the scan pose (what a grasp planner would see)
  <out>/frames/NNNNN_close.jpg   wrist camera right after the fingers closed
  <out>/data.jsonl               one row: true pose, grasp offset/yaw, finger position, lifted_m, label

    python3 testing/collect_grasp_data.py --gripper robotiq_2f_85 --object cube_5cm \
        --trials 300 --domain 91 --out ~/grasp_data/2f85_cube

Needs the sim free (one sim at a time). Appends to data.jsonl, so it can be resumed.
"""
import argparse
import json
import math
import os
import random
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402

LABEL_LIFT_M = 0.03     # the object must rise this far to count as held


class FrameGrabber:
    """Keeps the newest camera frame (BGR) so a trial can save it at an exact moment."""

    def __init__(self, node, topic):
        import numpy as np
        from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import Image
        self._np = np
        self._lock = threading.Lock()
        self._frame = None
        qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                         history=HistoryPolicy.KEEP_LAST, depth=1)
        node.create_subscription(Image, topic, self._cb, qos)

    def _cb(self, msg):
        import cv2
        img = self._np.frombuffer(msg.data, self._np.uint8).reshape(msg.height, msg.width, -1)
        if msg.encoding == "rgb8":
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        with self._lock:
            self._frame = img.copy()

    def latest(self):
        with self._lock:
            return None if self._frame is None else self._frame.copy()


def fold_quarter(angle):
    """A box looks the same every 90 degrees: fold to [-pi/4, pi/4)."""
    return (angle + math.pi / 4) % (math.pi / 2) - math.pi / 4


def run_trial(i, ex, grabber, obj, initial, args, out):
    import cv2
    rng = random.Random(args.seed + i)
    jx, jy = rng.uniform(-0.03, 0.03), rng.uniform(-0.03, 0.03)
    yaw = rng.uniform(-math.pi / 4, math.pi / 4) if args.random_yaw else 0.0
    bench.OBJECT_YAW = yaw
    bench.reset_object((initial[0] + jx, initial[1] + jy, initial[2]))
    before = bench.object_pose()
    if before is None:
        return None
    true_yaw = math.radians(bench.object_yaw_deg() or 0.0)

    # Look from the scan pose, like a planner would.
    ex.execute_task_list([{"action": "move_to_named_pose", "pose_name": "home"}])
    ex.move_to_pose(ex._make_downward_pose(
        bench.PICK_XY[0] + bench.SCAN_DX, bench.PICK_XY[1], bench.SCAN_TOOL_Z - ex._tcp_offset_z))
    time.sleep(1.5)
    scan = grabber.latest()

    # Grasp at a random offset from the true pose; that spread is what the labels teach.
    ox, oy = rng.uniform(-args.xy_spread, args.xy_spread), rng.uniform(-args.xy_spread, args.xy_spread)
    oyaw = rng.uniform(-args.yaw_spread, args.yaw_spread)
    grasp_yaw = fold_quarter(true_yaw + oyaw)
    px, py = before[0] + ox, before[1] + oy
    depth = min(0.03, 0.4 * obj["height"])
    pick_z = obj["top_z"] - depth

    reason, close_img, grip, lifted = "", None, float("nan"), float("nan")
    ex.open_gripper()
    above = ex._move_above(px, py, pick_z, grasp_yaw)
    if above is None:
        reason = "no_ik"
    elif not ex.move_to_pose(ex._make_downward_pose(px, py, pick_z + 0.01, grasp_yaw)):
        reason = "descend_failed"
    else:
        ex.close_gripper()
        time.sleep(0.6)
        close_img = grabber.latest()
        js = ex._latest_joint_state
        if js is not None and ex._gripper_joint_name in js.name:
            grip = js.position[js.name.index(ex._gripper_joint_name)]
        ex.move_to_pose(above)
        time.sleep(0.5)
        pose = bench.object_pose()
        lifted = (pose[2] - before[2]) if pose else float("nan")
    ex.open_gripper()
    ex.execute_task_list([{"action": "move_to_named_pose", "pose_name": "home"}])

    row = dict(trial=i, gripper=args.gripper, object=args.object, true_xy=[before[0], before[1]],
               true_yaw=true_yaw, offset_xy=[ox, oy], offset_yaw=oyaw, grasp_yaw=grasp_yaw,
               grip_pos=grip, lifted_m=lifted,
               label=int(not math.isnan(lifted) and lifted >= LABEL_LIFT_M), skipped=reason)
    frames = out / "frames"
    frames.mkdir(parents=True, exist_ok=True)
    if scan is not None:
        cv2.imwrite(str(frames / f"{i:05d}_scan.jpg"), scan, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if close_img is not None:
        cv2.imwrite(str(frames / f"{i:05d}_close.jpg"), close_img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    with open(out / "data.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gripper", default="robotiq_2f_85", choices=bench.DEFAULT_GRIPPERS)
    ap.add_argument("--object", default="cube_5cm", choices=list(bench.OBJECTS))
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--out", default=str(Path.home() / "grasp_data" / "run"))
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--settle", type=float, default=45.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--xy-spread", type=float, default=0.02, help="grasp offset range in x/y (m)")
    ap.add_argument("--yaw-spread", type=float, default=0.35, help="grasp yaw offset range (rad)")
    ap.add_argument("--launch-retries", type=int, default=3, help="relaunch the sim this often if it never serves goals")
    ap.add_argument("--random-yaw", action="store_true", help="rotate the object randomly each trial")
    args = ap.parse_args()

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    import rclpy
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from ur_llm_planner.motion_executor import MotionExecutor

    out = Path(args.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    done = 0
    if (out / "data.jsonl").exists():
        done = sum(1 for _ in open(out / "data.jsonl"))
    obj = bench.OBJECTS[args.object]
    bench.OBJECT = obj["model"]
    (bench.REPO / "logs").mkdir(exist_ok=True)

    rclpy.init()
    # A sim launch sometimes comes up without serving goals; relaunch instead of giving up.
    procs = node = executor = ex = grabber = None
    for attempt in range(1, args.launch_retries + 1):
        procs = bench.launch_sim(args.gripper, obj["world"], args.domain, args.settle)
        node = Node("collect_grasp_data")
        executor = SingleThreadedExecutor()
        executor.add_node(node)
        threading.Thread(target=executor.spin, daemon=True).start()
        ex = MotionExecutor(node)
        ex.set_gripper(args.gripper)
        grabber = FrameGrabber(node, "/camera_wrist/color/image_raw")
        if ex.wait_for_servers(timeout=60.0) and ex.execute_task_list(
                [{"action": "move_to_named_pose", "pose_name": "home"}]):
            break
        print(f"sim not serving goals (attempt {attempt}/{args.launch_retries})", flush=True)
        bench.stop_sim(procs)
        executor.shutdown()
        node.destroy_node()
        procs = None
    if procs is None:
        rclpy.shutdown()
        return 1
    try:
        initial = bench.object_pose()
        held = 0
        for i in range(done, args.trials):
            row = run_trial(i, ex, grabber, obj, initial, args, out)
            if row:
                held += row["label"]
            print(f"[collect] {i + 1}/{args.trials} label={row and row['label']} "
                  f"lifted={row and round(row['lifted_m'], 3)} grip={row and round(row['grip_pos'], 2)} "
                  f"{row and row['skipped']}", flush=True)
    finally:
        bench.stop_sim(procs)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
    print(f"done: {args.trials} trials in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
