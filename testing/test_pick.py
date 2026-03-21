#!/usr/bin/env python3
"""
Direct pick-and-place test — no LLM needed.

Sends hardcoded actions straight to MotionExecutor.
Run AFTER the simulation is up (controllers active):

    source install/setup.bash
    python3 testing/test_pick.py

You can override the target position:
    python3 testing/test_pick.py 0.25 0.10 0.08
"""

import sys
import threading
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

# Blue block position in colored_blocks.world (x, y, top-z)
DEFAULT_X = 0.25
DEFAULT_Y = 0.10
DEFAULT_Z = 0.08   # top surface of 8 cm block

# Where to place it
PLACE_X = 0.25
PLACE_Y = -0.15
PLACE_Z = 0.08


def main():
    x = float(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_X
    y = float(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_Y
    z = float(sys.argv[3]) if len(sys.argv) > 3 else DEFAULT_Z

    rclpy.init()
    node = Node("test_pick")

    # Spin in background so action callbacks work
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    # Import here so ROS is already init'd
    from ur_llm_planner.motion_executor import MotionExecutor
    ex = MotionExecutor(node)

    node.get_logger().info("Waiting for action servers (up to 15 s)...")
    ok = ex.wait_for_servers(timeout=15.0)
    if not ok:
        node.get_logger().error("Action servers not ready — is the simulation running?")
        executor.shutdown()
        rclpy.shutdown()
        return

    tasks = [
        {"action": "move_to_named_pose", "pose_name": "home"},
        {"action": "open_gripper"},
        {
            "action": "pick",
            "object_id": "blue_block",
            "object_x": x,
            "object_y": y,
            "object_z": z,
        },
        {"action": "place", "x": PLACE_X, "y": PLACE_Y, "z": PLACE_Z},
        {"action": "move_to_named_pose", "pose_name": "home"},
    ]

    node.get_logger().info(f"Picking object at ({x}, {y}, {z}), placing at ({PLACE_X}, {PLACE_Y}, {PLACE_Z})")
    success = ex.execute_task_list(tasks)
    node.get_logger().info(f"Result: {'SUCCESS' if success else 'FAILED'}")

    executor.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
