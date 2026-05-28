#!/usr/bin/env python3
"""
Closed-loop visual servoing node.

Continuously reads /ur_grasp/grasp_pose (updated by the grasp detector)
and the current end-effector pose from TF, then issues corrective
joint-trajectory commands until the EE is within tolerance.

This gives pose-based visual servoing (PBVS):
  - error = target_pose − current_ee_pose
  - while |error| > tol: move toward target in small Cartesian steps

Unlike a single one-shot MTC plan, this loop re-queries the grasp pose
each iteration — so it compensates for object drift or perception noise.

Usage:
    ros2 launch ur_visual_servo visual_servo.launch.py

Services:
    /visual_servo/start  (std_srvs/Trigger) — activate servo loop
    /visual_servo/stop   (std_srvs/Trigger) — deactivate loop

Parameters:
    servo_rate_hz     (float, 5.0)   — control loop rate
    xy_tolerance      (float, 0.015) — positional tolerance in X/Y [m]
    z_tolerance       (float, 0.010) — positional tolerance in Z [m]
    step_size         (float, 0.025) — max Cartesian step per iteration [m]
    grasp_offset_z    (float, 0.05)  — stop this far above the grasp pose
    auto_grasp        (bool, true)   — close gripper after convergence
    max_iterations    (int,  60)     — abort if not converged after N steps
"""

import math
import threading
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

import tf2_ros
import tf2_geometry_msgs  # noqa: F401  registers PoseStamped transforms

from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String
from std_srvs.srv import Trigger

SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

EE_FRAME = "tool0"
BASE_FRAME = "base_link"


class VisualServoNode(Node):
    def __init__(self):
        super().__init__("visual_servo_node")

        self.declare_parameter("servo_rate_hz",   5.0)
        self.declare_parameter("xy_tolerance",    0.015)
        self.declare_parameter("z_tolerance",     0.010)
        self.declare_parameter("step_size",       0.025)
        self.declare_parameter("grasp_offset_z",  0.05)
        self.declare_parameter("auto_grasp",      True)
        self.declare_parameter("max_iterations",  60)

        self._rate_hz        = self.get_parameter("servo_rate_hz").value
        self._xy_tol         = self.get_parameter("xy_tolerance").value
        self._z_tol          = self.get_parameter("z_tolerance").value
        self._step           = self.get_parameter("step_size").value
        self._grasp_offset_z = self.get_parameter("grasp_offset_z").value
        self._auto_grasp     = self.get_parameter("auto_grasp").value
        self._max_iter       = self.get_parameter("max_iterations").value

        self._target_pose: PoseStamped | None = None
        self._pose_lock = threading.Lock()
        self._active = False

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        self.create_subscription(
            PoseStamped, "/ur_grasp/grasp_pose", self._grasp_pose_cb, SENSOR_QOS
        )

        self._status_pub = self.create_publisher(String, "/visual_servo/status", 10)

        self.create_service(Trigger, "/visual_servo/start", self._start_cb)
        self.create_service(Trigger, "/visual_servo/stop",  self._stop_cb)

        from ur_llm_planner.motion_executor import MotionExecutor
        self._motion = MotionExecutor(self)

        self.get_logger().info(
            "VisualServoNode ready.  Call /visual_servo/start to activate."
        )

    # ── ROS callbacks ─────────────────────────────────────────────────────────

    def _grasp_pose_cb(self, msg: PoseStamped):
        with self._pose_lock:
            self._target_pose = msg

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

            # Refresh target each iteration (grasp detector updates continuously)
            with self._pose_lock:
                target = self._target_pose

            if target is None:
                time.sleep(dt)
                continue

            # Get current EE pose via TF
            current = self._get_ee_pose()
            if current is None:
                self.get_logger().warn("TF lookup failed — retrying.")
                time.sleep(dt)
                continue

            # Desired position: target + Z offset (hover before final descent)
            tx = target.pose.position.x
            ty = target.pose.position.y
            tz = target.pose.position.z + self._grasp_offset_z

            cx = current.pose.position.x
            cy = current.pose.position.y
            cz = current.pose.position.z

            ex = tx - cx
            ey = ty - cy
            ez = tz - cz

            xy_err = math.hypot(ex, ey)
            z_err  = abs(ez)

            self.get_logger().debug(
                f"  iter={iteration} err=({ex:.3f},{ey:.3f},{ez:.3f})"
                f" xy={xy_err:.3f} z={z_err:.3f}"
            )

            if xy_err < self._xy_tol and z_err < self._z_tol:
                self.get_logger().info(
                    f"Converged at ({cx:.3f},{cy:.3f},{cz:.3f}) after {iteration} steps."
                )
                self._publish_status("Servo: converged at hover position")
                break

            # Clamp step to max step size
            dist = math.sqrt(ex**2 + ey**2 + ez**2)
            scale = min(self._step / dist, 1.0) if dist > 1e-6 else 0.0

            goal_pose = self._make_downward_pose(
                cx + ex * scale,
                cy + ey * scale,
                cz + ez * scale,
            )
            ok = self._motion.move_to_pose(goal_pose, group="arm", timeout=10.0)
            if not ok:
                self.get_logger().warn(f"Step {iteration} planning failed — retrying.")

            time.sleep(dt)
        else:
            self.get_logger().warn(f"Max iterations ({self._max_iter}) reached without convergence.")
            self._publish_status("Servo: max iterations reached")

        # Final descent to grasp height
        if self._active and self._auto_grasp:
            self._execute_final_grasp(target)

        self._active = False

    def _execute_final_grasp(self, target: PoseStamped):
        self._publish_status("Servo: descending to grasp")
        self.get_logger().info("Descending to grasp…")

        self._motion.open_gripper()

        grasp_pose = self._make_downward_pose(
            target.pose.position.x,
            target.pose.position.y,
            target.pose.position.z + 0.01,
        )
        ok = self._motion.move_to_pose(grasp_pose, group="arm", timeout=15.0)
        if not ok:
            self.get_logger().error("Final descent failed.")
            self._publish_status("Servo: descent FAILED")
            return

        self._motion.close_gripper()
        self._publish_status("Servo: grasp complete")
        self.get_logger().info("Visual servo grasp complete.")

    # ── helpers ───────────────────────────────────────────────────────────────

    def _get_ee_pose(self) -> PoseStamped | None:
        try:
            tf = self._tf_buffer.lookup_transform(
                BASE_FRAME, EE_FRAME,
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
