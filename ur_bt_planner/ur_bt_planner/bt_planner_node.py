#!/usr/bin/env python3
"""
Behavior tree task planner node.

Replaces the flat task-list approach with a hierarchical BT that supports
retry, fallback, and parallel branches via py_trees.

Services:
    /bt/run_pick_place  (std_srvs/Trigger) — execute one pick-place cycle
    /bt/stop            (std_srvs/Trigger) — abort after current leaf

Parameters:
    pick_x, pick_y, pick_z   — object position in base_link [m]
    place_x, place_y, place_z — bin position in base_link [m]
    tick_rate_hz              — BT tick rate (default 10)
    use_compliant_grasp       — use force-limited close (default true)
"""

import threading
import time

import py_trees
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

from ur_bt_planner.bt_leaves import build_pick_place_tree
from ur_llm_planner.motion_executor import MotionExecutor


class BTPlannerNode(Node):
    def __init__(self):
        super().__init__("bt_planner_node")

        self.declare_parameter("pick_x",  0.35)
        self.declare_parameter("pick_y",  0.0)
        self.declare_parameter("pick_z",  0.05)
        self.declare_parameter("place_x", 0.15)
        self.declare_parameter("place_y", 0.30)
        self.declare_parameter("place_z", 0.08)
        self.declare_parameter("tick_rate_hz", 10.0)
        self.declare_parameter("use_compliant_grasp", True)

        self._pick_pose = {
            "id": "target",
            "x": self.get_parameter("pick_x").value,
            "y": self.get_parameter("pick_y").value,
            "z": self.get_parameter("pick_z").value,
        }
        self._place_pose = {
            "x": self.get_parameter("place_x").value,
            "y": self.get_parameter("place_y").value,
            "z": self.get_parameter("place_z").value,
        }
        self._tick_dt = 1.0 / self.get_parameter("tick_rate_hz").value

        self._running = False
        self._stop_flag = False

        self._status_pub = self.create_publisher(String, "/bt/status", 10)

        self.create_service(Trigger, "/bt/run_pick_place", self._run_cb)
        self.create_service(Trigger, "/bt/stop", self._stop_cb)

        self._executor_obj = MotionExecutor(self)

        self.get_logger().info(
            "BTPlannerNode ready. Call /bt/run_pick_place to execute."
        )

    def _run_cb(self, request, response):
        if self._running:
            response.success = False
            response.message = "Already running"
            return response
        threading.Thread(target=self._run_tree, daemon=True).start()
        response.success = True
        response.message = "BT started"
        return response

    def _stop_cb(self, request, response):
        self._stop_flag = True
        response.success = True
        response.message = "Stop requested"
        return response

    def _publish_status(self, text: str):
        self._status_pub.publish(String(data=text))

    def _run_tree(self):
        self._running = True
        self._stop_flag = False

        if not self._executor_obj.wait_for_servers(timeout=15.0):
            self.get_logger().error("Motion servers unavailable — aborting BT run.")
            self._publish_status("BT ERROR: motion servers not ready")
            self._running = False
            return

        tree = build_pick_place_tree(
            self._executor_obj, self._pick_pose, self._place_pose
        )
        tree.setup_with_descendants()

        self._publish_status("BT running")
        self.get_logger().info("BT tick loop starting")

        py_trees.display.ascii_tree(tree)

        while rclpy.ok() and not self._stop_flag:
            tree.tick_once()
            status = tree.status

            self.get_logger().info(f"BT tick → {status.name}")
            self._publish_status(f"BT: {status.name}")

            if status == py_trees.common.Status.SUCCESS:
                self.get_logger().info("BT completed successfully.")
                self._publish_status("BT: SUCCESS")
                break

            if status == py_trees.common.Status.FAILURE:
                self.get_logger().warn("BT failed.")
                self._publish_status("BT: FAILURE")
                break

            time.sleep(self._tick_dt)

        if self._stop_flag:
            self._publish_status("BT: stopped by user")

        self._running = False


def main(args=None):
    rclpy.init(args=args)
    node = BTPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
