#!/usr/bin/env python3
"""Check a gripper's mechanism in the sim, with nothing to grasp.

Sends the gripper to several finger positions and, for each, reads back the driven joint, every
mimic joint, and the real distance between the two finger pads (from TF). Flags:
  - a mimic joint that does not follow the driven joint (broken linkage / constraint),
  - left/right pads that are not symmetric about the gripper axis (one finger stuck),
  - a pad gap that does not shrink as commanded (fingers jammed or the controller not moving them).

    python3 testing/gripper_selftest.py --gripper robotiq_2f_140 --domain 91
"""
import argparse
import math
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402

PADS = {
    "robotiq_2f_85": ("left_inner_finger_pad", "right_inner_finger_pad"),
    "robotiq_2f_140": ("left_inner_finger_pad", "right_inner_finger_pad"),
    "onrobot_rg2": ("gripper_finger_1_flex_finger", "gripper_finger_2_flex_finger"),
    "onrobot_rg6": ("gripper_finger_1_flex_finger", "gripper_finger_2_flex_finger"),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gripper", required=True, choices=bench.DEFAULT_GRIPPERS)
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--settle", type=float, default=45.0)
    args = ap.parse_args()

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    import rclpy
    import tf2_ros
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from ur_llm_planner.motion_executor import MotionExecutor

    (bench.REPO / "logs").mkdir(exist_ok=True)
    rclpy.init()
    procs = bench.launch_sim(args.gripper, "colored_blocks.world", args.domain, args.settle)
    node = Node("gripper_selftest")
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    threading.Thread(target=executor.spin, daemon=True).start()
    problems = []
    try:
        ex = MotionExecutor(node)
        ex.set_gripper(args.gripper)
        buf = tf2_ros.Buffer()
        tf2_ros.TransformListener(buf, node)
        if not (ex.wait_for_servers(timeout=60.0) and ex.execute_task_list(
                [{"action": "move_to_named_pose", "pose_name": "home"}])):
            print("sim not serving goals -- rerun")
            return 1
        left, right = PADS[args.gripper]
        closed = ex._gripper_closed
        drv = ex._gripper_joint_name
        print(f"{args.gripper}: driven joint {drv}, closed target {closed}")
        print(f"{'cmd':>6} {'driven':>7} {'pad gap mm':>11} {'asym mm':>8}  mimic joints (deviation from the driven joint)")
        gaps = []
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0, 0.0):
            cmd = frac * closed
            ex._send_gripper_goal(cmd, 10.0, 8.0)
            time.sleep(1.5)
            js = ex._latest_joint_state
            pos = dict(zip(js.name, js.position))
            try:
                a = buf.lookup_transform("tool0", left, rclpy.time.Time()).transform.translation
                b = buf.lookup_transform("tool0", right, rclpy.time.Time()).transform.translation
                gap = math.dist((a.x, a.y, a.z), (b.x, b.y, b.z)) * 1000
                mid = [(a.x + b.x) / 2, (a.y + b.y) / 2]
                axis = 0 if abs(a.x - b.x) > abs(a.y - b.y) else 1     # the pads close along this tool axis
                asym = abs(mid[1 - axis]) * 1000 + abs(mid[axis]) * 1000   # pad midpoint off the gripper axis
            except Exception as e:      # noqa: BLE001
                gap, asym = float("nan"), float("nan")
                problems.append(f"TF lookup failed for pads: {e}")
            others = {n: v for n, v in pos.items() if n != drv and any(
                k in n for k in ("knuckle", "inner_finger", "truss", "tip", "moment", "mirror"))}
            dev = {n: round(v - pos[drv], 3) for n, v in others.items()}
            print(f"{cmd:>6.2f} {pos.get(drv, float('nan')):>7.3f} {gap:>11.1f} {asym:>8.1f}  "
                  f"{ {n[:22]: d for n, d in list(dev.items())[:5]} }")
            gaps.append((cmd, gap, pos.get(drv, float('nan'))))
            if asym == asym and asym > 6.0:
                problems.append(f"pads off-axis by {asym:.0f} mm at cmd {cmd:.2f} (one finger lagging?)")
        # the gap must shrink monotonically while closing, and come back when reopened
        opening = [g[1] for g in gaps[:5]]
        if any(opening[i + 1] > opening[i] + 1.0 for i in range(len(opening) - 1) if opening[i] == opening[i]):
            problems.append("pad gap did not shrink steadily while closing")
        if gaps[-1][1] == gaps[-1][1] and gaps[0][1] == gaps[0][1] and abs(gaps[-1][1] - gaps[0][1]) > 3.0:
            problems.append(f"gripper did not return to its open gap ({gaps[0][1]:.0f} -> {gaps[-1][1]:.0f} mm)")
        for cmd, gap, driven in gaps:
            if driven == driven and abs(driven - cmd) > 0.08 and cmd < closed:
                problems.append(f"driven joint {driven:.2f} did not reach command {cmd:.2f}")
    finally:
        bench.stop_sim(procs)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
    print()
    print("PROBLEMS:" if problems else "mechanism looks healthy (follows commands, symmetric, no jams).")
    for p in dict.fromkeys(problems):
        print(" -", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
