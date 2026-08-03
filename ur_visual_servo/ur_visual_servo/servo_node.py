#!/usr/bin/env python3
"""
Closed-loop visual servoing node.

Continuously reads /ur_grasp/grasp_pose (updated by the grasp detector)
and the current end-effector pose from TF, then issues corrective
joint-trajectory commands until the EE is within tolerance.

This gives pose-based visual servoing (PBVS):
  - error = target_pose − current_tcp_pose
  - while |error| > tol: move toward target in small Cartesian steps

TCP vs tool0
────────────
MoveIt / SRDF tip is tool0 (flange). The Robotiq 2F-85 fingertips sit
further along +tool0 Z (~0.14–0.15 m). Servoing tool0 to the object XY
therefore closes on air. This node tracks a virtual TCP =
tool0_origin + R_tool0 * tcp_offset_xyz, and commands tool0 goals that
place that TCP on the grasp target.

Usage:
    ros2 launch ur_visual_servo visual_servo.launch.py

Services:
    /visual_servo/start  (std_srvs/Trigger) — activate servo loop
    /visual_servo/stop   (std_srvs/Trigger) — deactivate loop

Parameters:
    servo_rate_hz     (float, 5.0)   — control loop rate
    xy_tolerance      (float, 0.006) — positional tolerance in X/Y [m]
    z_tolerance       (float, 0.010) — positional tolerance in Z [m]
    step_size         (float, 0.025) — max Cartesian step per iteration [m]
    grasp_offset_z    (float, 0.05)  — hover this far above the grasp (base Z)
    auto_grasp        (bool, true)   — close gripper after convergence
    max_iterations    (int,  60)     — abort if not converged after N steps
    ee_frame          (str, tool0)   — TF frame MoveIt actually drives
    tcp_offset_xyz    (float[3], [0,0,0.145]) — grasp TCP in ee_frame
    gripper_joint_name    (str, finger_joint) — joint checked after close to
                          verify grasp; use "gripper_joint" for OnRobot RG2/RG6
    gripper_fully_closed  (float, 0.8) — that joint's fully-closed position
                          (OnRobot RG2/RG6 use 1.3 — see their SRDF "closed" state)
    gripper_stall_margin  (float, 0.05) — stalling this far short of fully-closed
                          counts as "hit something" (a real grasp)
"""

import math
import threading
import time

import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

import tf2_ros
import tf2_geometry_msgs  # noqa: F401  registers PoseStamped transforms

from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from std_srvs.srv import Trigger

SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

BASE_FRAME = "base_link"


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _quat_to_rotation_matrix(q) -> np.ndarray:
    x2, y2, z2, w2 = q.x * q.x, q.y * q.y, q.z * q.z, q.w * q.w
    return np.array([
        [x2 - y2 - z2 + w2,           2 * (q.x * q.y - q.z * q.w), 2 * (q.x * q.z + q.y * q.w)],
        [2 * (q.x * q.y + q.z * q.w), -x2 + y2 - z2 + w2,          2 * (q.y * q.z - q.x * q.w)],
        [2 * (q.x * q.z - q.y * q.w), 2 * (q.y * q.z + q.x * q.w), -x2 - y2 + z2 + w2],
    ])


class VisualServoNode(Node):
    def __init__(self):
        super().__init__("visual_servo_node")

        self.declare_parameter("servo_rate_hz",   5.0)
        # 0.015 (1.5cm) is loose enough to "converge" while still off-center on
        # small objects (the test box is ~4.2cm across) — one finger clips the
        # object instead of centering around it, knocking it sideways rather
        # than gripping it. Tightened to stay well inside typical object radii.
        self.declare_parameter("xy_tolerance",    0.006)
        self.declare_parameter("z_tolerance",     0.010)
        self.declare_parameter("step_size",       0.025)
        self.declare_parameter("grasp_offset_z",  0.05)
        self.declare_parameter("auto_grasp",      True)
        self.declare_parameter("max_iterations",  60)
        self.declare_parameter("ee_frame",        "tool0")
        # Robotiq 2F-85: fingertip grasp center is ~145 mm along +tool0 Z from tool0
        # (base_link mount at +10 mm + ~135 mm through knuckles/pads when open).
        self.declare_parameter("tcp_offset_xyz",  [0.0, 0.0, 0.145])
        # Defaults match Robotiq 2F-85 (SRDF "closed" state: finger_joint=0.8).
        # For OnRobot RG2/RG6 set gripper_joint_name:=gripper_joint and
        # gripper_fully_closed:=1.3 (their SRDF "closed" state).
        self.declare_parameter("gripper_joint_name",   "finger_joint")
        self.declare_parameter("gripper_fully_closed", 0.8)
        self.declare_parameter("gripper_stall_margin", 0.05)

        self._rate_hz        = float(self.get_parameter("servo_rate_hz").value)
        self._xy_tol         = float(self.get_parameter("xy_tolerance").value)
        self._z_tol          = float(self.get_parameter("z_tolerance").value)
        self._step           = float(self.get_parameter("step_size").value)
        self._grasp_offset_z = float(self.get_parameter("grasp_offset_z").value)
        self._auto_grasp     = _as_bool(self.get_parameter("auto_grasp").value)
        self._max_iter       = int(self.get_parameter("max_iterations").value)
        self._ee_frame       = str(self.get_parameter("ee_frame").value)
        self._tcp_offset     = np.array(
            self.get_parameter("tcp_offset_xyz").value, dtype=np.float64
        )
        self._gripper_joint_name   = str(self.get_parameter("gripper_joint_name").value)
        self._gripper_fully_closed = float(self.get_parameter("gripper_fully_closed").value)
        self._gripper_stall_margin = float(self.get_parameter("gripper_stall_margin").value)

        self._target_pose: PoseStamped | None = None
        self._pose_lock = threading.Lock()
        self._active = False

        self._joint_state: JointState | None = None
        self._joint_state_lock = threading.Lock()

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        self.create_subscription(
            PoseStamped, "/ur_grasp/grasp_pose", self._grasp_pose_cb, SENSOR_QOS
        )
        self.create_subscription(
            JointState, "/joint_states", self._joint_state_cb, SENSOR_QOS
        )

        self._status_pub = self.create_publisher(String, "/visual_servo/status", 10)

        self.create_service(Trigger, "/visual_servo/start", self._start_cb)
        self.create_service(Trigger, "/visual_servo/stop",  self._stop_cb)

        from ur_llm_planner.motion_executor import MotionExecutor
        self._motion = MotionExecutor(self)

        self.get_logger().info(
            f"VisualServoNode ready — ee_frame={self._ee_frame}  "
            f"tcp_offset={self._tcp_offset.tolist()}.  "
            "Call /visual_servo/start to activate."
        )

    # ── ROS callbacks ─────────────────────────────────────────────────────────

    def _grasp_pose_cb(self, msg: PoseStamped):
        with self._pose_lock:
            self._target_pose = msg

    def _joint_state_cb(self, msg: JointState):
        with self._joint_state_lock:
            self._joint_state = msg

    def _start_cb(self, request, response):
        if self._active:
            response.success = False
            response.message = "Already active"
            return response
        threading.Thread(target=self._servo_loop, daemon=True).start()
        response.success = True
        response.message = "Visual servo started"
        return response

    def _stop_cb(self, request, response):
        self._active = False
        response.success = True
        response.message = "Stopping servo loop"
        return response

    # ── servo loop ────────────────────────────────────────────────────────────

    def _servo_loop(self):
        self._active = True
        dt = 1.0 / self._rate_hz

        self.get_logger().info("Waiting for /ur_grasp/grasp_pose…")
        while rclpy.ok() and self._active:
            with self._pose_lock:
                target = self._target_pose
            if target is not None:
                break
            time.sleep(0.2)

        if not self._active:
            return

        self.get_logger().info("Target acquired — starting servo approach.")
        self._publish_status("Servo: target acquired, approaching")

        if not self._motion.wait_for_servers(timeout=10.0):
            self.get_logger().error("Motion servers not available — aborting servo.")
            self._publish_status("ERROR: motion servers unavailable")
            self._active = False
            return

        for iteration in range(self._max_iter):
            if not self._active:
                break

            with self._pose_lock:
                target = self._target_pose

            if target is None:
                time.sleep(dt)
                continue

            ee = self._get_ee_pose()
            if ee is None:
                self.get_logger().warn("TF lookup failed — retrying.")
                time.sleep(dt)
                continue

            tcp = self._ee_to_tcp(ee)

            # Desired TCP: grasp target + hover offset in base Z
            tx = target.pose.position.x
            ty = target.pose.position.y
            tz = target.pose.position.z + self._grasp_offset_z

            cx = tcp.pose.position.x
            cy = tcp.pose.position.y
            cz = tcp.pose.position.z

            ex = tx - cx
            ey = ty - cy
            ez = tz - cz

            xy_err = math.hypot(ex, ey)
            z_err  = abs(ez)

            self.get_logger().debug(
                f"  iter={iteration} tcp_err=({ex:.3f},{ey:.3f},{ez:.3f})"
                f" xy={xy_err:.3f} z={z_err:.3f}"
            )

            if xy_err < self._xy_tol and z_err < self._z_tol:
                self.get_logger().info(
                    f"Converged TCP at ({cx:.3f},{cy:.3f},{cz:.3f}) after {iteration} steps."
                )
                self._publish_status("Servo: converged at hover position")
                break

            dist = math.sqrt(ex**2 + ey**2 + ez**2)
            scale = min(self._step / dist, 1.0) if dist > 1e-6 else 0.0

            # Step the TCP, then convert back to a tool0 command for MoveIt.
            next_tcp = self._make_downward_pose(
                cx + ex * scale,
                cy + ey * scale,
                cz + ez * scale,
            )
            goal_ee = self._tcp_to_ee(next_tcp)
            ok = self._motion.move_to_pose(goal_ee, group="arm", timeout=10.0)
            if not ok:
                self.get_logger().warn(f"Step {iteration} planning failed — retrying.")

            time.sleep(dt)
        else:
            self.get_logger().warn(f"Max iterations ({self._max_iter}) reached without convergence.")
            self._publish_status("Servo: max iterations reached")

        if self._active and self._auto_grasp:
            self._execute_final_grasp(target)

        self._active = False

    def _execute_final_grasp(self, target: PoseStamped):
        self._publish_status("Servo: descending to grasp")
        self.get_logger().info("Descending to grasp (TCP)…")

        self._motion.open_gripper()

        grasp_tcp = self._make_downward_pose(
            target.pose.position.x,
            target.pose.position.y,
            target.pose.position.z + 0.01,
        )
        grasp_ee = self._tcp_to_ee(grasp_tcp)
        ok = self._motion.move_to_pose(grasp_ee, group="arm", timeout=15.0)
        if not ok:
            self.get_logger().error("Final descent failed.")
            self._publish_status("Servo: descent FAILED")
            return

        self._motion.close_gripper()

        # close_gripper() alone can't tell success from "closed on air" — a
        # position controller commands full closure regardless of whether it
        # meets resistance. Read the actual finger position instead: stalling
        # short of fully-closed means the fingers hit something.
        time.sleep(0.5)
        grasped = self._verify_grasp()
        if grasped is True:
            self._publish_status("Servo: grasp complete (verified — object detected)")
            self.get_logger().info("Visual servo grasp complete — gripper stalled on object.")
        elif grasped is False:
            self._publish_status("Servo: grasp FAILED — gripper closed fully, likely missed object")
            self.get_logger().warn("Gripper closed fully with no resistance — likely missed the object.")
        else:
            self._publish_status("Servo: grasp complete (unverified — no /joint_states)")
            self.get_logger().info("Visual servo grasp complete (could not verify — no joint state).")

    def _verify_grasp(self) -> bool | None:
        """True if fingers stalled on something, False if closed fully, None if unknown."""
        with self._joint_state_lock:
            js = self._joint_state
        if js is None or self._gripper_joint_name not in js.name:
            return None
        position = js.position[js.name.index(self._gripper_joint_name)]
        return position < (self._gripper_fully_closed - self._gripper_stall_margin)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_ee_pose(self) -> PoseStamped | None:
        try:
            tf = self._tf_buffer.lookup_transform(
                BASE_FRAME, self._ee_frame,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.5),
            )
        except (tf2_ros.LookupException, tf2_ros.ExtrapolationException,
                tf2_ros.ConnectivityException) as exc:
            self.get_logger().debug(f"TF error: {exc}")
            return None

        pose = PoseStamped()
        pose.header.frame_id = BASE_FRAME
        pose.pose.position.x = tf.transform.translation.x
        pose.pose.position.y = tf.transform.translation.y
        pose.pose.position.z = tf.transform.translation.z
        pose.pose.orientation = tf.transform.rotation
        return pose

    def _ee_to_tcp(self, ee: PoseStamped) -> PoseStamped:
        """tool0 pose → virtual fingertip TCP pose in base_link."""
        R = _quat_to_rotation_matrix(ee.pose.orientation)
        offset_base = R @ self._tcp_offset
        tcp = PoseStamped()
        tcp.header = ee.header
        tcp.pose.orientation = ee.pose.orientation
        tcp.pose.position.x = ee.pose.position.x + float(offset_base[0])
        tcp.pose.position.y = ee.pose.position.y + float(offset_base[1])
        tcp.pose.position.z = ee.pose.position.z + float(offset_base[2])
        return tcp

    def _tcp_to_ee(self, tcp: PoseStamped) -> PoseStamped:
        """Desired TCP → tool0 goal MoveIt should drive (same orientation)."""
        R = _quat_to_rotation_matrix(tcp.pose.orientation)
        offset_base = R @ self._tcp_offset
        ee = PoseStamped()
        ee.header = tcp.header
        ee.pose.orientation = tcp.pose.orientation
        ee.pose.position.x = tcp.pose.position.x - float(offset_base[0])
        ee.pose.position.y = tcp.pose.position.y - float(offset_base[1])
        ee.pose.position.z = tcp.pose.position.z - float(offset_base[2])
        return ee

    @staticmethod
    def _make_downward_pose(x: float, y: float, z: float) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = BASE_FRAME
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.x = 1.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 0.0
        return pose

    def _publish_status(self, text: str):
        msg = String()
        msg.data = text
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = VisualServoNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
