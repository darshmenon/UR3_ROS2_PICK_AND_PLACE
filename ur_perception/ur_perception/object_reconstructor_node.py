#!/usr/bin/env python3
"""
object_reconstructor_node.py — multi-view point cloud fusion via a moving camera.

Registration here is TF-based, not ICP: the wrist camera's pose relative to
base_link is already known exactly from forward kinematics, so each incoming
frame is transformed straight into base_link and merged — no scan-matching
needed. Moving the arm (or just letting continuous_detect_hz spin) around an
object and accumulating frames fills in the occlusions any single viewpoint
misses (e.g. the camera_head stand only ever sees the object from one angle).

Services:
    /ur_perception/reconstruct/start  (std_srvs/Trigger) — clear buffer, start accumulating
    /ur_perception/reconstruct/stop   (std_srvs/Trigger) — stop, write PLY if save_path is set

Publishes:
    /ur_perception/reconstructed_points  (sensor_msgs/PointCloud2, base_link frame)

Subscribes:
    <camera_topic>       sensor_msgs/PointCloud2  (default /camera_wrist/depth/color/points)
    /ur_grasp/grasp_pose  geometry_msgs/PoseStamped  (optional — recenters the ROI filter)

Parameters:
    camera_topic  (str,   default "/camera_wrist/depth/color/points")
    voxel_size    (float, default 0.005)  merge grid size in metres
    roi_center    (float[3], default [0.35, 0.0, 0.06])  base_link-frame point to filter around
    roi_radius    (float, default 0.15)   keep points within this many metres of roi_center
    save_path     (str,   default "")     if set, write an ASCII PLY here on stop
"""

import threading
from typing import Optional

import numpy as np

import rclpy
from rclpy.node import Node

import tf2_ros

from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header
from std_srvs.srv import Trigger

from ur_grasp.cylinder_grasp_detector import decode_pointcloud2

BASE_FRAME = "base_link"


def _quat_to_rotation_matrix(q) -> np.ndarray:
    x2, y2, z2, w2 = q.x * q.x, q.y * q.y, q.z * q.z, q.w * q.w
    return np.array([
        [x2 - y2 - z2 + w2,           2 * (q.x * q.y - q.z * q.w), 2 * (q.x * q.z + q.y * q.w)],
        [2 * (q.x * q.y + q.z * q.w), -x2 + y2 - z2 + w2,          2 * (q.y * q.z - q.x * q.w)],
        [2 * (q.x * q.z - q.y * q.w), 2 * (q.y * q.z + q.x * q.w), -x2 - y2 + z2 + w2],
    ])


class VoxelMap:
    """Dict-backed voxel grid: one running-averaged [x,y,z,r,g,b] per cell."""

    def __init__(self, voxel_size: float):
        self.voxel_size = voxel_size
        self._cells: dict[tuple, list] = {}  # key -> [sum_x,sum_y,sum_z,sum_r,sum_g,sum_b,n]

    def add(self, points: np.ndarray) -> None:
        keys = np.floor(points[:, :3] / self.voxel_size).astype(np.int64)
        for key, pt in zip(map(tuple, keys), points):
            cell = self._cells.get(key)
            if cell is None:
                self._cells[key] = [*pt[:6], 1]
            else:
                for i in range(6):
                    cell[i] += pt[i]
                cell[6] += 1

    def as_array(self) -> np.ndarray:
        if not self._cells:
            return np.zeros((0, 6), dtype=np.float32)
        out = np.array(list(self._cells.values()), dtype=np.float32)
        n = out[:, 6:7]
        return out[:, :6] / n

    def clear(self) -> None:
        self._cells.clear()

    def __len__(self) -> int:
        return len(self._cells)


class ObjectReconstructorNode(Node):
    def __init__(self):
        super().__init__("object_reconstructor_node")

        self.declare_parameter("camera_topic", "/camera_wrist/depth/color/points")
        self.declare_parameter("voxel_size", 0.005)
        self.declare_parameter("roi_center", [0.35, 0.0, 0.06])
        self.declare_parameter("roi_radius", 0.15)
        self.declare_parameter("save_path", "")

        self._camera_topic = self.get_parameter("camera_topic").value
        self._roi_center = np.array(self.get_parameter("roi_center").value, dtype=np.float32)
        self._roi_radius = float(self.get_parameter("roi_radius").value)
        self._save_path = self.get_parameter("save_path").value

        self._voxels = VoxelMap(float(self.get_parameter("voxel_size").value))
        self._lock = threading.Lock()
        self._active = False
        self._frames_merged = 0

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        self.create_subscription(
            PointCloud2, self._camera_topic, self._cloud_cb,
            rclpy.qos.QoSPresetProfiles.SENSOR_DATA.value,
        )
        self.create_subscription(PoseStamped, "/ur_grasp/grasp_pose", self._grasp_pose_cb, 10)

        self._cloud_pub = self.create_publisher(
            PointCloud2, "/ur_perception/reconstructed_points", 10
        )

        self.create_service(Trigger, "/ur_perception/reconstruct/start", self._start_cb)
        self.create_service(Trigger, "/ur_perception/reconstruct/stop", self._stop_cb)

        self.get_logger().info(
            f"ObjectReconstructorNode ready — camera_topic={self._camera_topic}  "
            f"roi_center={self._roi_center.tolist()}  roi_radius={self._roi_radius}"
        )

    def _grasp_pose_cb(self, msg: PoseStamped) -> None:
        p = msg.pose.position
        self._roi_center = np.array([p.x, p.y, p.z], dtype=np.float32)

    def _start_cb(self, _req, response):
        with self._lock:
            self._voxels.clear()
            self._frames_merged = 0
            self._active = True
        response.success = True
        response.message = "Reconstruction started — accumulating frames"
        self.get_logger().info(response.message)
        return response

    def _stop_cb(self, _req, response):
        with self._lock:
            self._active = False
            n_points = len(self._voxels)
            n_frames = self._frames_merged
            cloud = self._voxels.as_array()

        save_path = self.get_parameter("save_path").value
        saved_msg = ""
        if save_path and n_points > 0:
            _write_ply(save_path, cloud)
            saved_msg = f", saved to {save_path}"

        response.success = True
        response.message = (
            f"Reconstruction stopped — {n_points} voxels from {n_frames} frames{saved_msg}"
        )
        self.get_logger().info(response.message)
        return response

    def _cloud_cb(self, msg: PointCloud2) -> None:
        with self._lock:
            active = self._active
        if not active:
            return

        cloud = decode_pointcloud2(msg)
        if cloud is None:
            return

        cloud = self._transform_to_base(cloud, msg.header.frame_id)
        if cloud is None:
            return

        dist = np.linalg.norm(cloud[:, :3] - self._roi_center, axis=1)
        cloud = cloud[dist <= self._roi_radius]
        if len(cloud) == 0:
            return

        with self._lock:
            self._voxels.add(cloud)
            self._frames_merged += 1
            fused = self._voxels.as_array()

        self._publish_cloud(fused)

    def _transform_to_base(self, cloud: np.ndarray, source_frame: str) -> Optional[np.ndarray]:
        if source_frame == BASE_FRAME:
            return cloud
        try:
            transform = self._tf_buffer.lookup_transform(
                BASE_FRAME, source_frame, rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.5),
            )
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f"TF {source_frame}->{BASE_FRAME} failed: {e}")
            return None

        r = _quat_to_rotation_matrix(transform.transform.rotation)
        t = transform.transform.translation
        translation = np.array([t.x, t.y, t.z])

        out = cloud.copy()
        out[:, :3] = cloud[:, :3] @ r.T + translation
        return out

    def _publish_cloud(self, cloud: np.ndarray) -> None:
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = BASE_FRAME

        fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name="rgb", offset=12, datatype=PointField.FLOAT32, count=1),
        ]

        n = len(cloud)
        data = np.zeros((n, 4), dtype=np.float32)
        data[:, :3] = cloud[:, :3]
        r = cloud[:, 3].astype(np.uint32)
        g = cloud[:, 4].astype(np.uint32)
        b = cloud[:, 5].astype(np.uint32)
        rgb_packed = (r << 16) | (g << 8) | b
        data[:, 3] = rgb_packed.view(np.float32)

        msg = PointCloud2()
        msg.header = header
        msg.height = 1
        msg.width = n
        msg.fields = fields
        msg.is_bigendian = False
        msg.point_step = 16
        msg.row_step = 16 * n
        msg.is_dense = True
        msg.data = data.tobytes()
        self._cloud_pub.publish(msg)


def _write_ply(path: str, cloud: np.ndarray) -> None:
    """Minimal ASCII PLY writer — viewable in MeshLab/CloudCompare/RViz."""
    with open(path, "w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(cloud)}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        for x, y, z, r, g, b in cloud:
            f.write(f"{x} {y} {z} {int(r)} {int(g)} {int(b)}\n")


def main(args=None):
    rclpy.init(args=args)
    node = ObjectReconstructorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
