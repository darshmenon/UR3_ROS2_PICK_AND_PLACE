#!/usr/bin/env python3
"""
Keyboard teleoperation for the UR3 arm.

JOINT MODE (default)
  1-6       select joint (shoulder_pan … wrist_3)
  W / S     jog selected joint  +step / -step
  O / P     gripper open / close

CARTESIAN MODE  (press C to toggle)
  W / S     move EE  +X / -X
  A / D     move EE  +Y / -Y
  Q / E     move EE  +Z / -Z
  O / P     gripper open / close

BOTH MODES
  C         toggle Joint ↔ Cartesian
  + / -     increase / decrease step size
  H         print this help
  Esc / ^C  quit
"""

import sys
import threading
import time

import numpy as np
import rclpy
from builtin_interfaces.msg import Duration
from geometry_msgs.msg import PoseStamped
from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import PositionIKRequest
from pynput import keyboard
from rclpy.node import Node
from sensor_msgs.msg import JointState
from tf2_ros import Buffer, TransformListener
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

ARM_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
GRIPPER_JOINT = "finger_joint"
GRIPPER_OPEN  = 0.0
GRIPPER_CLOSE = 0.80

STEP_SIZES   = [0.005, 0.01, 0.02, 0.05, 0.10]
DEFAULT_STEP = 2   # index into STEP_SIZES

HELP = """
╔══════════════════════════════════════════╗
║          UR3 Keyboard Teleop             ║
╠══════════════════════════════════════════╣
║  JOINT MODE (current)                    ║
║   1-6   select joint                     ║
║   W/S   jog +/-                          ║
║                                          ║
║  CARTESIAN MODE (press C to toggle)      ║
║   W/S   EE  +X/-X                        ║
║   A/D   EE  +Y/-Y                        ║
║   Q/E   EE  +Z/-Z                        ║
║                                          ║
║  BOTH MODES                              ║
║   O/P   gripper open/close               ║
║   +/-   step size (current: {step:.3f} m/rad) ║
║   C     toggle joint ↔ cartesian         ║
║   H     help                             ║
║   Esc   quit                             ║
╚══════════════════════════════════════════╝
"""


class KeyboardTeleop(Node):
    def __init__(self):
        super().__init__("keyboard_teleop")

        self._step_idx    = DEFAULT_STEP
        self._joint_sel   = 0          # which joint is active in joint mode
        self._cartesian   = False
        self._running     = True

        self._qpos  = np.zeros(6, dtype=np.float64)
        self._gripper_pos = GRIPPER_OPEN
        self._have_js = False

        self._arm_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10
        )
        self._gripper_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10
        )
        self.create_subscription(JointState, "/joint_states", self._js_cb, 10)

        self._tf_buffer   = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self)

        self._ik_client = self.create_client(GetPositionIK, "/compute_ik")

        self.get_logger().info("Keyboard teleop ready — press H for help")
        print(HELP.format(step=STEP_SIZES[self._step_idx]))

    # ------------------------------------------------------------------ #
    # Joint state callback
    # ------------------------------------------------------------------ #
    def _js_cb(self, msg: JointState):
        name_idx = {n: i for i, n in enumerate(msg.name)}
        for i, joint in enumerate(ARM_JOINTS):
            if joint in name_idx:
                self._qpos[i] = msg.position[name_idx[joint]]
        if GRIPPER_JOINT in name_idx:
            self._gripper_pos = msg.position[name_idx[GRIPPER_JOINT]]
        self._have_js = True

    # ------------------------------------------------------------------ #
    # Publish helpers
    # ------------------------------------------------------------------ #
    def _send_arm(self, positions, dt=0.15):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names  = ARM_JOINTS
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.time_from_start = Duration(
            sec=int(dt), nanosec=int((dt % 1) * 1e9)
        )
        msg.points = [pt]
        self._arm_pub.publish(msg)

    def _send_gripper(self, pos):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names  = [GRIPPER_JOINT]
        pt = JointTrajectoryPoint()
        pt.positions = [float(pos)]
        pt.time_from_start = Duration(sec=0, nanosec=500_000_000)
        msg.points = [pt]
        self._gripper_pub.publish(msg)

    # ------------------------------------------------------------------ #
    # Cartesian IK helper
    # ------------------------------------------------------------------ #
    def _cartesian_jog(self, dx=0.0, dy=0.0, dz=0.0):
        try:
            tf = self._tf_buffer.lookup_transform("base_link", "tool0", rclpy.time.Time())
        except Exception as e:
            self.get_logger().warn(f"TF lookup failed: {e}")
            return

        pose = PoseStamped()
        pose.header.frame_id = "base_link"
        pose.header.stamp    = self.get_clock().now().to_msg()
        t = tf.transform.translation
        r = tf.transform.rotation
        pose.pose.position.x    = t.x + dx
        pose.pose.position.y    = t.y + dy
        pose.pose.position.z    = t.z + dz
        pose.pose.orientation.x = r.x
        pose.pose.orientation.y = r.y
        pose.pose.orientation.z = r.z
        pose.pose.orientation.w = r.w

        req = GetPositionIK.Request()
        req.ik_request = PositionIKRequest()
        req.ik_request.group_name            = "arm"
        req.ik_request.pose_stamped          = pose
        req.ik_request.timeout.sec           = 1
        req.ik_request.avoid_collisions      = True

        future = self._ik_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=1.5)
        if not future.done():
            self.get_logger().warn("IK timed out")
            return

        resp = future.result()
        if resp.error_code.val != 1:
            self.get_logger().warn(f"IK failed (error {resp.error_code.val})")
            return

        sol = resp.solution.joint_state
        name_idx = {n: i for i, n in enumerate(sol.name)}
        target = list(self._qpos)
        for i, joint in enumerate(ARM_JOINTS):
            if joint in name_idx:
                target[i] = sol.position[name_idx[joint]]
        self._send_arm(target)

    # ------------------------------------------------------------------ #
    # Keypress handler (runs in pynput thread)
    # ------------------------------------------------------------------ #
    def on_press(self, key):
        if not self._have_js:
            return

        step = STEP_SIZES[self._step_idx]

        try:
            ch = key.char.lower() if hasattr(key, "char") and key.char else None
        except AttributeError:
            ch = None

        # --- quit ---
        if key == keyboard.Key.esc:
            self._running = False
            return False  # stops pynput listener

        # --- toggle mode ---
        if ch == "c":
            self._cartesian = not self._cartesian
            mode = "CARTESIAN" if self._cartesian else "JOINT"
            print(f"\n  → Switched to {mode} mode")
            return

        # --- step size ---
        if ch in ("+", "="):
            self._step_idx = min(self._step_idx + 1, len(STEP_SIZES) - 1)
            print(f"\n  step = {STEP_SIZES[self._step_idx]:.3f}")
            return
        if ch == "-":
            self._step_idx = max(self._step_idx - 1, 0)
            print(f"\n  step = {STEP_SIZES[self._step_idx]:.3f}")
            return

        # --- help ---
        if ch == "h":
            print(HELP.format(step=STEP_SIZES[self._step_idx]))
            return

        # --- gripper (both modes) ---
        if ch == "o":
            self._send_gripper(GRIPPER_OPEN)
            print("\n  gripper → OPEN")
            return
        if ch == "p":
            self._send_gripper(GRIPPER_CLOSE)
            print("\n  gripper → CLOSE")
            return

        # --- joint select ---
        if ch in ("1","2","3","4","5","6"):
            self._joint_sel = int(ch) - 1
            print(f"\n  joint → {ARM_JOINTS[self._joint_sel]}")
            return

        # --- motion ---
        if self._cartesian:
            if ch == "w":
                self._cartesian_jog(dx=+step)
            elif ch == "s":
                self._cartesian_jog(dx=-step)
            elif ch == "a":
                self._cartesian_jog(dy=+step)
            elif ch == "d":
                self._cartesian_jog(dy=-step)
            elif ch == "q":
                self._cartesian_jog(dz=+step)
            elif ch == "e":
                self._cartesian_jog(dz=-step)
        else:
            target = self._qpos.copy()
            if ch == "w":
                target[self._joint_sel] += step
            elif ch == "s":
                target[self._joint_sel] -= step
            else:
                return
            self._send_arm(target)
            print(
                f"\r  {ARM_JOINTS[self._joint_sel]}: "
                f"{np.degrees(target[self._joint_sel]):.1f}°  ",
                end="", flush=True,
            )

    def run(self):
        with keyboard.Listener(on_press=self.on_press) as listener:
            while self._running and rclpy.ok():
                rclpy.spin_once(self, timeout_sec=0.05)
            listener.stop()


def main(args=None):
    rclpy.init(args=args)
    node = KeyboardTeleop()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
