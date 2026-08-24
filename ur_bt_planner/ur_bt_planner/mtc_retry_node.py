#!/usr/bin/env python3
"""
BT-driven retry wrapper for ur_mtc_pick_place_demo's mtc_node.

Separate from bt_planner_node.py (which drives the direct-move_group
MotionExecutor pipeline with fixed pick/place XYZ params). This node has no
motion logic of its own — it only retries mtc_node's run_pick_place service
until it succeeds or max_attempts is exhausted, since mtc_node already owns
perception, grasp-candidate search, and collision-aware planning.

Mirrors bt_planner_node.py's async pattern: /mtc_bt/run starts the retry
tree and returns immediately (a full run can take minutes); actual progress
is on /mtc_bt/status.

Services:
    /mtc_bt/run   (std_srvs/Trigger) — start the retry tree
    /mtc_bt/stop  (std_srvs/Trigger) — stop retrying after the current attempt

Parameters:
    max_attempts       — retries before giving up (default 5)
    mtc_service_name   — mtc_node's service to call (default "run_pick_place")
    tick_rate_hz        — BT tick rate (default 2.0; each tick's leaf call
                          itself blocks for the whole pick-place attempt, so
                          this only paces the retry-decorator's outer loop)
"""

import threading
import time

import py_trees
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

from ur_bt_planner.bt_leaves import build_mtc_retry_tree


class MTCRetryNode(Node):
    def __init__(self):
        super().__init__("mtc_retry_node")

        self.declare_parameter("max_attempts", 5)
        self.declare_parameter("mtc_service_name", "run_pick_place")
        self.declare_parameter("tick_rate_hz", 2.0)

        self._max_attempts = self.get_parameter("max_attempts").value
        self._service_name = self.get_parameter("mtc_service_name").value
        self._tick_dt = 1.0 / self.get_parameter("tick_rate_hz").value

        self._running = False
        self._stop_flag = False

        self._status_pub = self.create_publisher(String, "/mtc_bt/status", 10)
        self.create_service(Trigger, "/mtc_bt/run", self._run_cb)
        self.create_service(Trigger, "/mtc_bt/stop", self._stop_cb)

        self.get_logger().info(
            f"MTCRetryNode ready (max_attempts={self._max_attempts}, "
            f"service='{self._service_name}'). Call /mtc_bt/run to execute."
        )

    def _run_cb(self, request, response):
        if self._running:
            response.success = False
            response.message = "Already running"
            return response
        threading.Thread(target=self._run_tree, daemon=True).start()
        response.success = True
        response.message = "Retry tree started"
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

        tree = build_mtc_retry_tree(
            self, max_attempts=self._max_attempts, service_name=self._service_name
        )
        tree.setup_with_descendants()
        py_trees.display.ascii_tree(tree)

        self._publish_status("MTC retry running")

        while rclpy.ok() and not self._stop_flag:
            tree.tick_once()
            status = tree.status
            self.get_logger().info(f"MTC retry tick -> {status.name}")
            self._publish_status(f"MTC retry: {status.name}")

            if status == py_trees.common.Status.SUCCESS:
                self.get_logger().info("MTC pick-and-place succeeded.")
                self._publish_status("MTC retry: SUCCESS")
                break
            if status == py_trees.common.Status.FAILURE:
                self.get_logger().warn(f"MTC pick-and-place failed after {self._max_attempts} attempt(s).")
                self._publish_status("MTC retry: FAILURE")
                break

            time.sleep(self._tick_dt)

        if self._stop_flag:
            self._publish_status("MTC retry: stopped by user")

        self._running = False


def main(args=None):
    rclpy.init(args=args)
    node = MTCRetryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
