#!/usr/bin/env python3
"""
test_grasp.py — test grasp detection node.

1. Calls /ur_grasp/detect service
2. Prints detected grasp pose
3. Optionally executes the grasp using MotionExecutor

Usage
─────
  source install/setup.bash
  # Terminal 1: sim running
  ros2 launch ur_gazebo ur.gazebo.launch.py

  # Terminal 2: grasp node
  ros2 run ur_grasp grasp_node

  # Terminal 3: test
  python3 testing/test_grasp.py              # detect only
  python3 testing/test_grasp.py --execute    # detect + pick
  python3 testing/test_grasp.py --colour red # filter by colour
"""

import argparse
import sys
import threading

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger
from geometry_msgs.msg import PoseStamped


class GraspTester(Node):
    def __init__(self, colour: str, execute: bool):
        super().__init__("grasp_tester")
        self._colour = colour
        self._execute = execute
        self._done = threading.Event()
        self._grasp_pose: PoseStamped = None

        self._detect_client = self.create_client(Trigger, "/ur_grasp/detect")
        self._grasp_sub = self.create_subscription(
            PoseStamped, "/ur_grasp/grasp_pose", self._grasp_cb, 10
        )

        threading.Thread(target=self._run, daemon=True).start()

    def _grasp_cb(self, msg: PoseStamped):
        self._grasp_pose = msg

    def _run(self):
        # Set colour param on grasp node if needed
        if self._colour != "any":
            import subprocess
            subprocess.run(
                ["ros2", "param", "set", "/grasp_node", "colour", self._colour],
                capture_output=True
            )

        self.get_logger().info("Waiting for /ur_grasp/detect service...")
        if not self._detect_client.wait_for_service(timeout_sec=10.0):
            self.get_logger().error("Grasp detection service not available. Is grasp_node running?")
            self._done.set()
            return

        self.get_logger().info("Calling /ur_grasp/detect...")
        req = Trigger.Request()
        future = self._detect_client.call_async(req)

        event = threading.Event()
        future.add_done_callback(lambda _: event.set())
        if not event.wait(timeout=15.0):
            self.get_logger().error("Detection timed out.")
            self._done.set()
            return

        resp = future.result()
        if not resp.success:
            print(f"\n❌ Detection failed: {resp.message}")
            self._done.set()
            return

        print(f"\n✅ {resp.message}")

        if self._execute and self._grasp_pose is not None:
            self._execute_grasp(self._grasp_pose)
        elif self._execute:
            self.get_logger().warn("No grasp pose received on topic yet.")

        self._done.set()

    def _execute_grasp(self, pose: PoseStamped):
        from ur_llm_planner.motion_executor import MotionExecutor
        self.get_logger().info("Executing grasp...")
        executor = MotionExecutor(self)
        if not executor.wait_for_servers(timeout=15.0):
            self.get_logger().error("MoveIt servers not ready.")
            return

        px = pose.pose.position
        task = {
            "action": "pick",
            "object_id": f"{self._colour}_object",
            "object_x": px.x,
            "object_y": px.y,
            "object_z": px.z,
        }
        ok = executor._execute_pick(task)
        print(f"  Pick: {'✅ OK' if ok else '❌ FAILED'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--colour",  default="any", help="Colour filter: red/blue/green/any")
    ap.add_argument("--execute", action="store_true", help="Execute the detected grasp")
    args = ap.parse_args()

    rclpy.init()
    node = GraspTester(colour=args.colour, execute=args.execute)

    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    node._done.wait(timeout=30.0)
    rclpy.shutdown()
    spin_thread.join(timeout=2.0)


if __name__ == "__main__":
    main()
