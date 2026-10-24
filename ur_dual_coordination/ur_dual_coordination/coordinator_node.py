#!/usr/bin/env python3
"""ROS 2 node: whole-body coordination of the two UR3 arms carrying one object.

    ros2 launch ur_dual_coordination dual_coordination.launch.py

Bring both hands to the object (e.g. with the dual MTC pipeline or the joint controllers), then:

    ros2 service call /dual/grasp   std_srvs/srv/Trigger {}      # freeze the hands' relative pose = hold the object
    ros2 topic pub --once /dual/object_target geometry_msgs/msg/PoseStamped \
        "{header: {frame_id: world}, pose: {position: {x: 0.2, y: 0.0, z: 0.35}, orientation: {w: 1.0}}}"
    ros2 service call /dual/release std_srvs/srv/Trigger {}      # stop commanding

Every 20 ms it solves all 12 joints together (see controller.py) and streams a short joint trajectory to
/left_arm_controller and /right_arm_controller. Status is on /dual/status.
"""
import math
import threading
from typing import Dict, Optional

import numpy as np
import pinocchio as pin
import rclpy
from builtin_interfaces.msg import Duration
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from ur_dual_coordination.controller import ControllerConfig, DualArmController
from ur_dual_coordination.kinematics import DualArm


def min_jerk(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5


class DualCoordinator(Node):
    def __init__(self):
        super().__init__("dual_coordinator")
        self.declare_parameter("rate_hz", 50.0)
        self.declare_parameter("max_object_speed", 0.08)      # m/s along the object path
        self.declare_parameter("min_move_time", 1.5)          # s
        self.declare_parameter("max_joint_speed", 1.0)        # rad/s
        self.declare_parameter("joint_state_timeout", 0.5)    # s: stop commanding if joint states go stale
        self.declare_parameter("left_topic", "/left_arm_controller/joint_trajectory")
        self.declare_parameter("right_topic", "/right_arm_controller/joint_trajectory")

        self._lock = threading.Lock()
        self.dual: Optional[DualArm] = None
        self.ctl: Optional[DualArmController] = None
        self.q: Optional[np.ndarray] = None
        self._q_stamp = 0.0
        self._mode = "idle"                  # idle | holding
        self._path = None                    # (start SE3, goal SE3, t0, duration)

        latched = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.create_subscription(String, "/robot_description", self._on_description, latched)
        self.create_subscription(JointState, "/joint_states", self._on_joint_state, 20)
        self.create_subscription(PoseStamped, "/dual/object_target", self._on_target, 10)
        self.create_service(Trigger, "/dual/grasp", self._grasp)
        self.create_service(Trigger, "/dual/release", self._release)
        self._left_pub = self.create_publisher(JointTrajectory, self.get_parameter("left_topic").value, 10)
        self._right_pub = self.create_publisher(JointTrajectory, self.get_parameter("right_topic").value, 10)
        self._status_pub = self.create_publisher(String, "/dual/status", 10)
        self.create_timer(1.0 / self.get_parameter("rate_hz").value, self._tick)
        self.get_logger().info("DualCoordinator waiting for /robot_description and /joint_states")

    # -- inputs ----------------------------------------------------------------------------------------
    def _on_description(self, msg: String):
        if self.dual is not None:
            return
        try:
            self.dual = DualArm(msg.data)
            cfg = ControllerConfig(max_joint_speed=self.get_parameter("max_joint_speed").value)
            self.ctl = DualArmController(self.dual, cfg)
            self.get_logger().info(f"Dual-arm model loaded ({self.dual.nv} joints)")
        except Exception as e:            # noqa: BLE001
            self.get_logger().error(f"could not build the dual-arm model from /robot_description: {e}")

    def _on_joint_state(self, msg: JointState):
        if self.dual is None:
            return
        with self._lock:
            if self.q is None:
                self.q = np.zeros(self.dual.nv)
            for name, pos in zip(msg.name, msg.position):
                col = self.dual.col.get(name)
                if col is not None:
                    self.q[col] = pos
            self._q_stamp = self.get_clock().now().nanoseconds * 1e-9

    def _on_target(self, msg: PoseStamped):
        if self._mode != "holding" or self.q is None:
            self.get_logger().warn("ignoring /dual/object_target: call /dual/grasp first")
            return
        p = msg.pose
        goal = pin.SE3(pin.Quaternion(p.orientation.w, p.orientation.x, p.orientation.y, p.orientation.z).matrix(),
                       np.array([p.position.x, p.position.y, p.position.z]))
        with self._lock:
            start = self.ctl.object_pose(self.q)
        dist = float(np.linalg.norm(goal.translation - start.translation))
        ang = float(np.linalg.norm(pin.log3(start.rotation.T @ goal.rotation)))
        dur = max(self.get_parameter("min_move_time").value,
                  dist / self.get_parameter("max_object_speed").value, ang / 0.4)
        self._path = (start, goal, self.get_clock().now().nanoseconds * 1e-9, dur)
        self.get_logger().info(f"moving the object {dist * 100:.1f} cm / {math.degrees(ang):.0f} deg in {dur:.1f} s")

    def _grasp(self, request, response):
        if self.q is None or self.ctl is None:
            response.success, response.message = False, "no joint states / robot model yet"
            return response
        with self._lock:
            self.ctl.set_grasp(self.q.copy())
            obj = self.ctl.object_pose(self.q)
        self._mode, self._path = "holding", (obj, obj, 0.0, 1.0)
        response.success = True
        response.message = f"holding: hands frozen at their current relative pose; object at {obj.translation.round(3).tolist()}"
        return response

    def _release(self, request, response):
        self._mode, self._path = "idle", None
        response.success, response.message = True, "released"
        return response

    # -- control loop ----------------------------------------------------------------------------------
    def _tick(self):
        if self._mode != "holding" or self.ctl is None or self.q is None or self._path is None:
            return
        now = self.get_clock().now().nanoseconds * 1e-9
        if now - self._q_stamp > self.get_parameter("joint_state_timeout").value:
            self._status("joint states are stale: not commanding")
            return
        dt = 1.0 / self.get_parameter("rate_hz").value
        start, goal, t0, dur = self._path
        s = min_jerk((now - t0) / dur) if t0 > 0 else 1.0
        target = pin.SE3(start.rotation @ pin.exp3(s * pin.log3(start.rotation.T @ goal.rotation)),
                         start.translation + s * (goal.translation - start.translation))
        with self._lock:
            st = self.ctl.step(self.q.copy(), target, dt=dt)
        self._publish(st.q, dt)
        self._status(f"obj err {st.obj_error * 1000:.1f} mm, hand err {st.rel_error * 1000:.2f} mm, "
                     f"arm distance {st.min_distance * 100:.0f} cm" + (f", limits: {st.saturated}" if st.saturated else ""))

    def _publish(self, q_cmd: np.ndarray, dt: float):
        for side, pub, cols in (("left", self._left_pub, self.dual.left_cols), ("right", self._right_pub, self.dual.right_cols)):
            msg = JointTrajectory()
            msg.joint_names = [self.dual.joint_names[c] for c in cols]
            pt = JointTrajectoryPoint()
            pt.positions = [float(q_cmd[c]) for c in cols]
            ns = int(2.5 * dt * 1e9)
            pt.time_from_start = Duration(sec=ns // 10 ** 9, nanosec=ns % 10 ** 9)
            msg.points = [pt]
            pub.publish(msg)

    def _status(self, text: str):
        self._status_pub.publish(String(data=f"[{self._mode}] {text}"))


def main(args=None):
    rclpy.init(args=args)
    node = DualCoordinator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
