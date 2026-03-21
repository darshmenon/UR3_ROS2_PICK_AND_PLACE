#!/usr/bin/env python3
"""Standalone tkinter GUI for UR3 arm control + camera feed.

Run after sourcing the workspace:
    python3 scripts/robot_gui.py
"""

import threading
import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import Image as RosImage, JointState

from ur_llm_planner.motion_executor import (
    MotionExecutor,
    _ARM_JOINTS,
    _ARM_JOINT_LIMITS,
)

_JOINT_SHORT_NAMES = ["Pan", "Lift", "Elbow", "Wrist 1", "Wrist 2", "Wrist 3"]


class RobotGUI:
    """Tkinter GUI: camera feed on the left, arm/gripper controls on the right."""

    def __init__(self, node: Node, motion: MotionExecutor):
        self._node = node
        self._motion = motion
        self._lock = threading.Lock()
        self._latest_photo = None       # ImageTk.PhotoImage (must stay alive)
        self._joint_positions = [0.0] * 6

        node.create_subscription(
            RosImage, "/camera_head/color/image_raw", self._image_cb, 10
        )
        node.create_subscription(
            JointState, "/joint_states", self._joint_state_cb, 10
        )

        self._root = tk.Tk()
        self._root.title("UR3 Robot Control")
        self._root.resizable(True, True)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = self._root

        # ── Top area: camera (left) + controls (right) ──────────────────
        top = tk.Frame(root)
        top.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Camera panel
        cam_frame = tk.LabelFrame(top, text="Camera Feed")
        cam_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self._cam_label = tk.Label(cam_frame, bg="black", text="No feed", fg="gray",
                                   width=53, height=15)
        self._cam_label.pack(fill=tk.BOTH, expand=True)

        # Controls panel
        ctrl = tk.Frame(top)
        ctrl.pack(side=tk.LEFT, fill=tk.Y)

        # Preset poses
        preset_frame = tk.LabelFrame(ctrl, text="Preset Poses")
        preset_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Button(preset_frame, text="Home", width=10, bg="#e8f5e9",
                  command=lambda: self._go_named("home")).pack(
                      side=tk.LEFT, padx=4, pady=4)
        tk.Button(preset_frame, text="Ready", width=10, bg="#e3f2fd",
                  command=lambda: self._go_named("ready")).pack(
                      side=tk.LEFT, padx=4, pady=4)

        # Gripper
        grip_frame = tk.LabelFrame(ctrl, text="Gripper")
        grip_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Button(grip_frame, text="Open", width=8, bg="#c8e6c9",
                  command=lambda: self._async_call(self._motion.open_gripper)).pack(
                      side=tk.LEFT, padx=4, pady=4)
        tk.Button(grip_frame, text="Half", width=8,
                  command=lambda: self._async_call(self._motion.half_close_gripper)).pack(
                      side=tk.LEFT, padx=4, pady=4)
        tk.Button(grip_frame, text="Close", width=8, bg="#ffccbc",
                  command=lambda: self._async_call(self._motion.close_gripper)).pack(
                      side=tk.LEFT, padx=4, pady=4)

        # Joint sliders
        joint_frame = tk.LabelFrame(ctrl, text="Joint Control (radians)")
        joint_frame.pack(fill=tk.X, pady=(0, 6))

        self._slider_vars = []
        self._cur_labels = []

        for i, (short, limits) in enumerate(zip(_JOINT_SHORT_NAMES, _ARM_JOINT_LIMITS)):
            row = tk.Frame(joint_frame)
            row.pack(fill=tk.X, padx=4, pady=2)

            tk.Label(row, text=short, width=8, anchor="w").pack(side=tk.LEFT)

            var = tk.DoubleVar(value=0.0)
            self._slider_vars.append(var)

            ttk.Scale(row, from_=limits[0], to=limits[1],
                      orient=tk.HORIZONTAL, variable=var, length=200).pack(
                          side=tk.LEFT, padx=4)

            cur = tk.Label(row, text="cur:  0.000", width=12, anchor="w", fg="#1565c0")
            cur.pack(side=tk.LEFT)
            self._cur_labels.append(cur)

        # Send / sync buttons
        btn_row = tk.Frame(ctrl)
        btn_row.pack(fill=tk.X, pady=(0, 6))

        tk.Button(btn_row, text="Send Joints", bg="#bbdefb", width=14,
                  command=self._send_joints).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(btn_row, text="Sync from Robot", width=14,
                  command=self._sync_sliders).pack(side=tk.LEFT)

        # ── Status bar ───────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self._status_var,
                 bd=1, relief=tk.SUNKEN, anchor="w").pack(
                     fill=tk.X, side=tk.BOTTOM, padx=4, pady=(0, 4))

    # ------------------------------------------------------------------
    # ROS callbacks (background thread)
    # ------------------------------------------------------------------

    def _image_cb(self, msg: RosImage):
        try:
            arr = np.frombuffer(msg.data, dtype=np.uint8).reshape(
                msg.height, msg.width, -1)
            if msg.encoding in ("bgr8", "bgra8"):
                arr = arr[:, :, ::-1]           # BGR → RGB
            img = Image.fromarray(arr[:, :, :3])
            img.thumbnail((480, 270))
            photo = ImageTk.PhotoImage(image=img)
            with self._lock:
                self._latest_photo = photo
        except Exception:
            pass

    def _joint_state_cb(self, msg: JointState):
        for i, jname in enumerate(_ARM_JOINTS):
            if jname in msg.name:
                idx = msg.name.index(jname)
                self._joint_positions[i] = msg.position[idx]

    # ------------------------------------------------------------------
    # Periodic GUI update (tkinter thread)
    # ------------------------------------------------------------------

    def _tick(self):
        # Camera
        with self._lock:
            photo = self._latest_photo
        if photo is not None:
            self._cam_label.config(image=photo, text="")
            self._cam_label.image = photo       # keep reference

        # Joint labels
        for i, val in enumerate(self._joint_positions):
            self._cur_labels[i].config(text=f"cur: {val:+.3f}")

        self._root.after(100, self._tick)       # 10 Hz refresh

    # ------------------------------------------------------------------
    # Button actions (spawn threads so UI stays responsive)
    # ------------------------------------------------------------------

    def _go_named(self, pose_name: str):
        self._set_status(f"Moving to '{pose_name}'...")
        def run():
            ok = self._motion.move_to_named_pose("arm", pose_name)
            self._set_status("Done" if ok else f"Failed to reach '{pose_name}'")
        threading.Thread(target=run, daemon=True).start()

    def _send_joints(self):
        values = [var.get() for var in self._slider_vars]
        self._set_status(f"Sending joints: {[f'{v:.2f}' for v in values]}")
        def run():
            ok = self._motion._move_to_joint_values("arm", values)
            self._set_status("Done" if ok else "Joint move failed")
        threading.Thread(target=run, daemon=True).start()

    def _sync_sliders(self):
        for i, val in enumerate(self._joint_positions):
            self._slider_vars[i].set(val)
        self._set_status("Sliders synced from robot")

    def _async_call(self, fn):
        self._set_status(f"{fn.__name__}...")
        def run():
            ok = fn()
            self._set_status("Done" if ok else f"{fn.__name__} failed")
        threading.Thread(target=run, daemon=True).start()

    def _set_status(self, msg: str):
        self._root.after(0, lambda: self._status_var.set(msg))

    # ------------------------------------------------------------------

    def run(self):
        self._root.after(100, self._tick)
        self._root.mainloop()


def main():
    rclpy.init()
    node = Node("robot_gui")

    ros_executor = MultiThreadedExecutor()
    ros_executor.add_node(node)

    spin_thread = threading.Thread(target=ros_executor.spin, daemon=True)
    spin_thread.start()

    motion = MotionExecutor(node)
    node.get_logger().info("Waiting for action servers (up to 10 s)...")
    motion.wait_for_servers(timeout=10.0)

    gui = RobotGUI(node, motion)
    try:
        gui.run()
    finally:
        ros_executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
