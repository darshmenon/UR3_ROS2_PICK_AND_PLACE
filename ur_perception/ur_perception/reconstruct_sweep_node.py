#!/usr/bin/env python3
"""
reconstruct_sweep_node.py — occlusion-aware wrist-camera orbit while reconstructing.

Starts reconstruction, then repeatedly picks the next joint-space viewpoint that
best covers the least-observed azimuth sector around the ROI (from the live
fused cloud), dwells so frames merge, and finally stops reconstruction.

Usage:
  ros2 launch ur_perception reconstruct_sweep.launch.py colour:=red
"""

from __future__ import annotations

import time
from typing import List, Optional

import numpy as np

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from action_msgs.msg import GoalStatus
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from sensor_msgs.msg import PointCloud2
from std_srvs.srv import Trigger
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

from ur_grasp.cylinder_grasp_detector import decode_pointcloud2

_ARM_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]

# Candidate viewpoints (joint space). Each is tagged with the approximate
# azimuth (radians, base XY) it looks toward relative to the table workspace.
# Occlusion-aware selection ranks unused candidates by how empty that sector is.
#
# wrist_2 is negated relative to the values this list originally shipped with:
# those pointed the wrist camera ~165-172 deg away from the workspace (verified
# live via TF — cos_angle between the camera's optical axis and the
# camera->roi_center direction was -0.94 to -0.97, i.e. facing almost exactly
# backward). Negating wrist_2 alone flips that to +0.84 to +0.99 (camera
# looking straight at the target) while leaving position (shoulder_pan/lift/
# elbow, which were already reasonable) untouched.
_CANDIDATES: List[dict] = [
    {"joints": [0.35, -1.10, 1.35, -1.70, -1.57, 0.20], "azimuth": 0.6},
    {"joints": [0.10, -1.00, 1.25, -1.60, -1.57, 0.00], "azimuth": 0.15},
    {"joints": [-0.20, -1.10, 1.35, -1.70, -1.57, -0.20], "azimuth": -0.5},
    {"joints": [0.00, -1.20, 1.40, -1.75, -1.57, 0.00], "azimuth": 0.0},
    {"joints": [0.25, -0.95, 1.20, -1.55, -1.57, 0.15], "azimuth": 0.4},
    {"joints": [-0.35, -1.05, 1.30, -1.65, -1.57, -0.25], "azimuth": -0.8},
    {"joints": [0.45, -1.15, 1.40, -1.75, -1.57, 0.30], "azimuth": 0.9},
]

# Conservative joint position limits (radians), from
# ur_description/config/ur3/joint_limits.yaml. elbow_joint is intentionally
# tighter than its raw +-360deg URDF limit (see that file's comment on why:
# the shoulder_lift joint physically blocks elbow rotation past ~+-1pi).
_JOINT_LIMITS = {
    "shoulder_pan_joint": (-2 * np.pi, 2 * np.pi),
    "shoulder_lift_joint": (-2 * np.pi, 2 * np.pi),
    "elbow_joint": (-np.pi, np.pi),
    "wrist_1_joint": (-2 * np.pi, 2 * np.pi),
    "wrist_2_joint": (-2 * np.pi, 2 * np.pi),
    "wrist_3_joint": (-2 * np.pi, 2 * np.pi),
}


def _joints_within_limits(positions: List[float]) -> Optional[str]:
    """Returns None if all positions are within _JOINT_LIMITS, else an error string."""
    for name, pos in zip(_ARM_JOINTS, positions):
        lo, hi = _JOINT_LIMITS[name]
        if not (lo <= pos <= hi):
            return f"{name}={pos:.3f} outside [{lo:.3f}, {hi:.3f}]"
    return None


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _azimuth_hist(cloud: np.ndarray, center_xy: np.ndarray, n_bins: int = 8) -> np.ndarray:
    if cloud is None or len(cloud) == 0:
        return np.zeros(n_bins, dtype=np.float64)
    dxy = cloud[:, :2] - center_xy
    ang = np.arctan2(dxy[:, 1], dxy[:, 0])
    bins = ((ang + np.pi) / (2 * np.pi) * n_bins).astype(np.int64) % n_bins
    hist = np.bincount(bins, minlength=n_bins).astype(np.float64)
    return hist


class ReconstructSweepNode(Node):
    def __init__(self):
        super().__init__("reconstruct_sweep_node")

        self.declare_parameter("dwell_sec", 1.5)
        self.declare_parameter("seg_sec", 3.0)
        self.declare_parameter("auto_start", True)
        self.declare_parameter("max_views", 5)
        self.declare_parameter("roi_center", [0.35, 0.0, 0.06])
        self.declare_parameter("occlusion_aware", True)
        self.declare_parameter("reconstructed_topic", "/ur_perception/reconstructed_points")

        self._dwell = float(self.get_parameter("dwell_sec").value)
        self._seg = float(self.get_parameter("seg_sec").value)
        self._auto_start = _as_bool(self.get_parameter("auto_start").value)
        self._max_views = int(self.get_parameter("max_views").value)
        self._roi_center = np.array(self.get_parameter("roi_center").value, dtype=np.float64)
        self._occlusion_aware = _as_bool(self.get_parameter("occlusion_aware").value)
        self._recon_topic = self.get_parameter("reconstructed_topic").value

        self._latest_cloud: Optional[np.ndarray] = None

        self._traj_client = ActionClient(
            self, FollowJointTrajectory, "/arm_controller/follow_joint_trajectory"
        )
        self._start_cli = self.create_client(Trigger, "/ur_perception/reconstruct/start")
        self._stop_cli = self.create_client(Trigger, "/ur_perception/reconstruct/stop")
        self.create_subscription(PointCloud2, self._recon_topic, self._recon_cb, 10)

        self.get_logger().info(
            f"ReconstructSweepNode ready — max_views={self._max_views}  "
            f"occlusion_aware={self._occlusion_aware}  dwell={self._dwell}s"
        )

    def _recon_cb(self, msg: PointCloud2) -> None:
        cloud = decode_pointcloud2(msg)
        if cloud is not None:
            self._latest_cloud = cloud

    def run_sweep(self) -> bool:
        if not self._wait_services():
            return False
        if not self._call_trigger(self._start_cli, "start"):
            return False

        remaining = [dict(c) for c in _CANDIDATES]
        visited = 0

        while visited < self._max_views and remaining:
            idx = self._pick_next_index(remaining)
            choice = remaining.pop(idx)
            joints = choice["joints"]
            self.get_logger().info(
                f"View {visited + 1}/{self._max_views}  az={choice['azimuth']:.2f}  "
                + ", ".join(f"{j:.2f}" for j in joints)
            )
            if not self._send_joints(joints):
                self.get_logger().warn("Trajectory failed — stopping reconstruction early")
                self._call_trigger(self._stop_cli, "stop")
                return False

            end = time.monotonic() + self._dwell
            while time.monotonic() < end:
                rclpy.spin_once(self, timeout_sec=0.1)
            visited += 1

        return self._call_trigger(self._stop_cli, "stop")

    def _pick_next_index(self, remaining: List[dict]) -> int:
        """Pick candidate whose azimuth sector is least covered in the fused cloud."""
        if not self._occlusion_aware or self._latest_cloud is None or len(remaining) == 1:
            return 0

        hist = _azimuth_hist(self._latest_cloud, self._roi_center[:2], n_bins=8)
        best_i = 0
        best_score = float("inf")
        for i, cand in enumerate(remaining):
            # Map candidate azimuth to hist bin
            ang = float(cand["azimuth"])
            b = int(((ang + np.pi) / (2 * np.pi) * 8)) % 8
            # Prefer emptiest bin; slight preference for neighbors being empty too
            score = hist[b] + 0.3 * hist[(b - 1) % 8] + 0.3 * hist[(b + 1) % 8]
            if score < best_score:
                best_score = score
                best_i = i
        return best_i

    def _wait_services(self) -> bool:
        self.get_logger().info("Waiting for reconstruct start/stop services...")
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            if self._start_cli.service_is_ready() and self._stop_cli.service_is_ready():
                break
            rclpy.spin_once(self, timeout_sec=0.2)
        else:
            self.get_logger().error("reconstruct start/stop services not available")
            return False

        self.get_logger().info("Waiting for /arm_controller/follow_joint_trajectory...")
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            if self._traj_client.server_is_ready():
                return True
            rclpy.spin_once(self, timeout_sec=0.2)
        self.get_logger().error("arm_controller FollowJointTrajectory not available")
        return False

    def _call_trigger(self, client, label: str) -> bool:
        future = client.call_async(Trigger.Request())
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and not future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
        result = future.result() if future.done() else None
        if result is None:
            self.get_logger().error(f"reconstruct/{label} call failed (no response)")
            return False
        if not result.success:
            self.get_logger().error(f"reconstruct/{label}: {result.message}")
            return False
        self.get_logger().info(f"reconstruct/{label}: {result.message}")
        return True

    def _send_joints(self, positions: List[float]) -> bool:
        violation = _joints_within_limits(positions)
        if violation is not None:
            self.get_logger().error(
                f"Refusing to send trajectory — joint limit violated: {violation}"
            )
            return False

        goal = FollowJointTrajectory.Goal()
        traj = JointTrajectory()
        traj.joint_names = list(_ARM_JOINTS)
        point = JointTrajectoryPoint()
        point.positions = [float(p) for p in positions]
        sec = int(self._seg)
        nanosec = int((self._seg - sec) * 1e9)
        point.time_from_start = Duration(sec=sec, nanosec=nanosec)
        traj.points = [point]
        goal.trajectory = traj

        send_future = self._traj_client.send_goal_async(goal)
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and not send_future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
        goal_handle = send_future.result() if send_future.done() else None
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error("Trajectory goal rejected")
            return False

        result_future = goal_handle.get_result_async()
        deadline = time.monotonic() + self._seg + 10.0
        while time.monotonic() < deadline and not result_future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
        result = result_future.result() if result_future.done() else None
        if result is None:
            self.get_logger().error("Trajectory result timed out")
            return False
        if result.status != GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().error(f"Trajectory status={result.status}")
            return False
        return True


def main(args=None):
    rclpy.init(args=args)
    node = ReconstructSweepNode()
    try:
        if node._auto_start:
            ok = node.run_sweep()
            node.get_logger().info("Sweep finished successfully" if ok else "Sweep failed")
        else:
            rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
