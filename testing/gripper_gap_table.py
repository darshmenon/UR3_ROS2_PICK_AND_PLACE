#!/usr/bin/env python3
"""Measure finger gap versus actuated joint angle for a gripper in the headless sim.

    python3 testing/gripper_gap_table.py --gripper robotiq_2f_140 --stroke 0.14 --max 0.7

Commands the gripper to a range of finger_joint angles with no object in the way and reads the distance between the two
inner finger pad frames from TF. The open pose is calibrated to the known stroke (so pad thickness drops out). Prints the
table and a C++/YAML-ready list. mtc_node.cpp used a LINEAR model, joint = closed * (1 - gap / stroke); the real
four-bar linkage is not linear, so the pads close looser or tighter than intended on a given object.
"""
import argparse
import math
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gripper", default="robotiq_2f_140")
    ap.add_argument("--stroke", type=float, default=0.14, help="nominal stroke, m (for the linear-model column)")
    ap.add_argument("--max", type=float, default=0.7, help="largest finger_joint angle to command")
    ap.add_argument("--steps", type=int, default=15)
    ap.add_argument("--left", default="left_inner_finger_pad")
    ap.add_argument("--right", default="right_inner_finger_pad")
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--world", default="colored_cylinder.world")
    args = ap.parse_args()

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    import rclpy
    import tf2_ros
    from control_msgs.action import GripperCommand
    from rclpy.action import ActionClient
    from rclpy.node import Node

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import benchmark_mtc as mtc

    sim = bench.launch_sim(args.gripper, args.world, args.domain, 45)
    rows = []
    try:
        mtc.wait_controllers(args.domain, timeout=300.0)
        rclpy.init()
        node = Node("gripper_gap_table")
        buf = tf2_ros.Buffer()
        tf2_ros.TransformListener(buf, node)
        client = ActionClient(node, GripperCommand, "/gripper_controller/gripper_cmd")
        if not client.wait_for_server(timeout_sec=60):
            raise SystemExit("no /gripper_controller/gripper_cmd")

        def dist():
            for _ in range(40):
                rclpy.spin_once(node, timeout_sec=0.1)
                try:
                    a = buf.lookup_transform("world", args.left, rclpy.time.Time())
                    b = buf.lookup_transform("world", args.right, rclpy.time.Time())
                    pa, pb = a.transform.translation, b.transform.translation
                    return math.dist((pa.x, pa.y, pa.z), (pb.x, pb.y, pb.z))
                except Exception:
                    continue
            return None

        state = {}
        from sensor_msgs.msg import JointState
        node.create_subscription(JointState, "/joint_states",
                                 lambda m: state.update(zip(m.name, m.position)), 10)

        def joint_pos():
            for _ in range(10):
                rclpy.spin_once(node, timeout_sec=0.1)
            return state.get("finger_joint")

        for i in range(args.steps + 1):
            q = args.max * i / args.steps
            goal = GripperCommand.Goal()
            goal.command.position = q
            goal.command.max_effort = 40.0
            fut = client.send_goal_async(goal)
            rclpy.spin_until_future_complete(node, fut, timeout_sec=10)
            # wait until the pad distance stops changing (the fingers can take several seconds, and stall)
            d, prev, still, t0 = None, None, 0, time.time()
            while time.time() - t0 < 20 and still < 4:
                time.sleep(0.5)
                d = dist()
                still = still + 1 if (d is not None and prev is not None and abs(d - prev) < 2e-4) else 0
                prev = d
            actual = joint_pos()
            rows.append((q, d, actual))
            print(f"command={q:.3f}  actual finger_joint={actual}  pad_distance={d}  settled_in={time.time() - t0:.1f}s",
                  flush=True)
    finally:
        bench.stop_sim(sim)
    rows = [(q, d) for q, d, _ in rows]
    if not rows or rows[0][1] is None:
        print("no data")
        return 1
    # Pad frames sit behind the contact faces. Calibrate to the CLOSED pose (faces touching, gap 0): this matches what the
    # real MTC grasps do (a 4.9 cm cylinder is held when closing to ~0.475 rad). Calibrating to the open stroke instead
    # would say the pads stay 6.7 cm apart there and could not hold it.
    c = rows[-1][1]
    print(f"\ncalibration: pad distance at max close = {rows[-1][1]:.4f} m taken as gap 0 (open gap then {rows[0][1] - c:.4f} m)")
    print("\n joint(rad)  gap(m)   linear-model gap(m)")
    closed = args.max
    for q, d in rows:
        if d is None:
            continue
        print(f" {q:8.3f}  {d - c:7.4f}   {args.stroke * (1 - q / closed):7.4f}")
    pts = [(q, d - c) for q, d in rows if d is not None]
    print("\ngap -> joint table (gap ascending), for mtc_node:")
    print("gripper_gap_table: [" + ", ".join(f"{g:.4f}, {q:.4f}" for q, g in sorted(pts, key=lambda p: p[1])) + "]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
