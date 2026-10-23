#!/usr/bin/env python3
"""Measure where the finger pads really are at the grasp pose, versus where we aimed.

Moves to the grasp pose over the object exactly like a benchmark pick, then reads (from TF) the
pad frames in base_link and (from Gazebo) the object's true position:

  aimed      the point the executor was told to put the fingertips at
  open       pad midpoint with the gripper open      (should equal aimed)
  closed     pad midpoint after closing on the object (should equal the object centre)
  tool0      actual flange position vs commanded     (arm tracking error)

Differences are the real TCP error in x, y, z. Use them to correct the per-gripper tcp offset.

    python3 testing/measure_tcp.py --gripper robotiq_2f_140 --object cube_5cm --domain 91
"""
import argparse
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
WORLD_Z_OFFSET = 1.0     # gazebo world z = base_link z + 1.0 (cube top 1.105 world = 0.105 base)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gripper", required=True, choices=bench.DEFAULT_GRIPPERS)
    ap.add_argument("--object", default="cube_5cm", choices=list(bench.OBJECTS))
    ap.add_argument("--domain", type=int, default=91)
    ap.add_argument("--settle", type=float, default=45.0)
    args = ap.parse_args()

    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    import rclpy
    import tf2_ros
    from rclpy.executors import SingleThreadedExecutor
    from rclpy.node import Node
    from ur_llm_planner.motion_executor import MotionExecutor

    obj = bench.OBJECTS[args.object]
    bench.OBJECT = obj["model"]
    (bench.REPO / "logs").mkdir(exist_ok=True)
    rclpy.init()
    procs = bench.launch_sim(args.gripper, obj["world"], args.domain, args.settle)
    node = Node("measure_tcp")
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    threading.Thread(target=executor.spin, daemon=True).start()
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

        def at(frame):
            t = buf.lookup_transform("base_link", frame, rclpy.time.Time()).transform.translation
            return (t.x, t.y, t.z)

        def mm(v):
            return " ".join(f"{1000 * c:+7.1f}" for c in v)

        depth = min(0.03, 0.4 * obj["height"])
        pick_z = obj["top_z"] - depth
        aimed = (bench.PICK_XY[0], bench.PICK_XY[1], pick_z + 0.01)    # what _execute_pick aims at
        ex.open_gripper()
        if ex._move_above(*bench.PICK_XY, pick_z) is None:
            print("could not reach the hover pose")
            return 1
        ex.move_to_pose(ex._make_downward_pose(*aimed))
        time.sleep(2.0)

        a, b = at(left), at(right)
        mid = tuple((p + q) / 2 for p, q in zip(a, b))
        tool = at("tool0")
        cmd_tool = (aimed[0], aimed[1], aimed[2] + ex._tcp_offset_z)
        cube = bench.object_pose()
        cube_b = (cube[0], cube[1], cube[2] - WORLD_Z_OFFSET) if cube else None
        print(f"{args.gripper} / {args.object}   tcp offset used {ex._tcp_offset_z:.3f}   (x y z in mm, base_link)")
        print(f"  aimed fingertip point            {mm(aimed)}")
        print(f"  pad midpoint, gripper OPEN       {mm(mid)}   error vs aimed {mm([m - t for m, t in zip(mid, aimed)])}")
        print(f"  flange tool0 actual vs commanded {mm(tool)}   error {mm([m - t for m, t in zip(tool, cmd_tool)])}")
        if cube_b:
            print(f"  object centre (gazebo truth)     {mm(cube_b)}")
        table_z = obj["top_z"] - obj["height"]
        print(f"  table top z {1000 * table_z:+.0f} mm; open pad centres z {1000 * a[2]:+.0f} / {1000 * b[2]:+.0f}")

        ex.close_gripper()
        time.sleep(1.5)
        a2, b2 = at(left), at(right)
        mid2 = tuple((p + q) / 2 for p, q in zip(a2, b2))
        gap = sum((p - q) ** 2 for p, q in zip(a2, b2)) ** 0.5
        cube2 = bench.object_pose()
        cube2_b = (cube2[0], cube2[1], cube2[2] - WORLD_Z_OFFSET) if cube2 else None
        print(f"  pad midpoint, CLOSED on object   {mm(mid2)}   pad gap {1000 * gap:.0f} mm")
        if cube2_b:
            print(f"  object centre after closing      {mm(cube2_b)}")
            print(f"  pad midpoint minus object centre {mm([m - c for m, c in zip(mid2, cube2_b)])}   <- real TCP error")
            moved = [1000 * (c2 - c1) for c1, c2 in zip(cube_b, cube2_b)] if cube_b else None
            if moved:
                print(f"  object pushed by closing         {' '.join(f'{v:+7.1f}' for v in moved)}")
        print(f"  closed pad centre z {1000 * a2[2]:+.0f} / {1000 * b2[2]:+.0f} mm "
              f"(table {1000 * table_z:+.0f} mm: {1000 * (min(a2[2], b2[2]) - table_z):+.0f} mm above)")
        ex.open_gripper()
        ex.execute_task_list([{"action": "move_to_named_pose", "pose_name": "home"}])
    finally:
        bench.stop_sim(procs)
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
