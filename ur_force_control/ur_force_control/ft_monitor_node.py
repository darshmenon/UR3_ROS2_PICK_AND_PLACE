#!/usr/bin/env python3
"""
Force/torque monitor and compliant grasping node.

Watches finger_joint effort from /joint_states to detect contact during
gripper closure. Publishes effort and contact state, and provides a
/ft/compliant_close service that closes the gripper until contact is
detected (effort spike) rather than closing to a fixed position.

Topics published:
    /ft/finger_effort   (std_msgs/Float32) — raw finger_joint effort [Nm]
    /ft/contact_detected (std_msgs/Bool)   — true when effort > threshold

Services:
    /ft/compliant_close (std_srvs/Trigger) — close until contact

Parameters:
    effort_threshold  (float, 3.0)  — effort [Nm] that signals contact
    close_step        (float, 0.05) — gripper position step per iteration
    step_interval_s   (float, 0.15) — seconds between steps
    max_effort_limit  (float, 8.0)  — max_effort sent to gripper controller
"""

import threading
import time

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from action_msgs.msg import GoalStatus
from control_msgs.action import GripperCommand
from sensor_msgs.msg import JointState
from std_msgs.msg import Bool, Float32
from std_srvs.srv import Trigger

FINGER_JOINT = "finger_joint"
GRIPPER_ACTION = "/gripper_controller/gripper_cmd"


class FTMonitorNode(Node):
    def __init__(self):
        super().__init__("ft_monitor_node")

        self.declare_parameter("effort_threshold", 3.0)
        self.declare_parameter("close_step", 0.05)
        self.declare_parameter("step_interval_s", 0.15)
        self.declare_parameter("max_effort_limit", 8.0)

        self._threshold = self.get_parameter("effort_threshold").value
        self._close_step = self.get_parameter("close_step").value
        self._step_interval = self.get_parameter("step_interval_s").value
        self._max_effort = self.get_parameter("max_effort_limit").value

        self._finger_effort: float = 0.0
        self._finger_position: float = 0.0
        self._effort_lock = threading.Lock()

        self._effort_pub = self.create_publisher(Float32, "/ft/finger_effort", 10)
        self._contact_pub = self.create_publisher(Bool, "/ft/contact_detected", 10)

        self.create_subscription(JointState, "/joint_states", self._js_cb, 10)

        self._gripper_client = ActionClient(self, GripperCommand, GRIPPER_ACTION)

        self.create_service(Trigger, "/ft/compliant_close", self._compliant_close_cb)

        self.create_timer(0.05, self._publish_state)

        self.get_logger().info(
            f"FTMonitorNode ready. threshold={self._threshold} Nm, "
            f"step={self._close_step}"
        )

    def _js_cb(self, msg: JointState):
        if FINGER_JOINT in msg.name:
            idx = msg.name.index(FINGER_JOINT)
            with self._effort_lock:
                self._finger_effort = (
                    msg.effort[idx] if idx < len(msg.effort) else 0.0
                )
                self._finger_position = msg.position[idx] if idx < len(msg.position) else 0.0

    def _publish_state(self):
        with self._effort_lock:
            effort = self._finger_effort

        self._effort_pub.publish(Float32(data=abs(effort)))

        contact = abs(effort) > self._threshold
        self._contact_pub.publish(Bool(data=contact))

    def _compliant_close_cb(self, request, response):
        threading.Thread(target=self._do_compliant_close, daemon=True).start()
        response.success = True
        response.message = "Compliant close started"
        return response

    def _do_compliant_close(self):
        if not self._gripper_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("Gripper server not available")
            return

        with self._effort_lock:
            current_pos = self._finger_position

        target = current_pos
        max_pos = 0.8

        self.get_logger().info("Compliant close: stepping gripper closed")

        while target < max_pos:
            target = min(target + self._close_step, max_pos)

            ok = self._send_gripper_step(target)
            if not ok:
                break

            time.sleep(self._step_interval)

            with self._effort_lock:
                effort = abs(self._finger_effort)

            if effort > self._threshold:
                self.get_logger().info(
                    f"Contact detected! effort={effort:.2f} Nm at pos={target:.3f}"
                )
                self._contact_pub.publish(Bool(data=True))
                return

        self.get_logger().info("Compliant close complete (no contact or fully closed)")

    def _send_gripper_step(self, position: float) -> bool:
        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = self._max_effort

        future = self._gripper_client.send_goal_async(goal)
        event = threading.Event()
        future.add_done_callback(lambda _: event.set())
        if not event.wait(timeout=3.0):
            return False

        handle = future.result()
        if not handle or not handle.accepted:
            return False

        result_future = handle.get_result_async()
        event2 = threading.Event()
        result_future.add_done_callback(lambda _: event2.set())
        event2.wait(timeout=3.0)
        return True


def main(args=None):
    rclpy.init(args=args)
    node = FTMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
