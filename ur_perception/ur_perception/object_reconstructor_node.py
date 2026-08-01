#!/usr/bin/env python3
"""
object_reconstructor_node.py — multi-view point cloud fusion via a moving camera.

Registration is TF-based (not ICP): each RGBD frame is transformed into
base_link using the camera pose from forward kinematics and merged into a
voxel grid. Optional second camera (e.g. fixed head) is fused the same way.

Services:
    /ur_perception/reconstruct/start  (std_srvs/Trigger)
    /ur_perception/reconstruct/stop   (std_srvs/Trigger)

Publishes:
    /ur_perception/reconstructed_points  (sensor_msgs/PointCloud2, base_link)

Parameters: see declare_parameter() block in ObjectReconstructorNode.__init__.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from scipy.spatial import cKDTree

import rclpy
from rclpy.node import Node
from rclpy.time import Time

import tf2_ros

from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header
from std_srvs.srv import Trigger

from ur_grasp.cylinder_grasp_detector import decode_pointcloud2, colour_mask

BASE_FRAME = "base_link"


def _quat_to_rotation_matrix(q) -> np.ndarray:
    x2, y2, z2, w2 = q.x * q.x, q.y * q.y, q.z * q.z, q.w * q.w
    return np.array([
        [x2 - y2 - z2 + w2,           2 * (q.x * q.y - q.z * q.w), 2 * (q.x * q.z + q.y * q.w)],
        [2 * (q.x * q.y + q.z * q.w), -x2 + y2 - z2 + w2,          2 * (q.y * q.z - q.x * q.w)],
        [2 * (q.x * q.z - q.y * q.w), 2 * (q.y * q.z + q.x * q.w), -x2 - y2 + z2 + w2],
    ])


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


def _statistical_outlier_filter(
    cloud: np.ndarray,
    nb_neighbors: int = 20,
    std_ratio: float = 2.0,
) -> np.ndarray:
    """Keep points whose mean kNN distance is within mean+std_ratio*std.

    Uses a KDTree (O(n log n)) rather than a full pairwise distance matrix
    (O(n^2) time AND memory) — the same class of executor-starvation bug
    VoxelMap.add() used to have (see its docstring): a slow per-frame filter
    on the single-threaded executor blocks this node's own service callbacks
    (reconstruct/start, reconstruct/stop) along with TF, not just merging.
    """
    n = len(cloud)
    if n < max(nb_neighbors + 1, 10):
        return cloud
    xyz = cloud[:, :3].astype(np.float64)
    tree = cKDTree(xyz)
    k = min(nb_neighbors + 1, n)
    dist, _ = tree.query(xyz, k=k)
    mean_dist = dist[:, 1:].mean(axis=1)  # exclude self (distance 0 at column 0)
    mu = float(mean_dist.mean())
    sigma = float(mean_dist.std())
    keep = mean_dist <= (mu + std_ratio * sigma)
    return cloud[keep]


class VoxelMap:
    """Dict-backed voxel grid: one running-averaged [x,y,z,r,g,b] per cell."""

    _BITS = 21
    _OFFSET = 1 << (_BITS - 1)
    _MASK = (1 << _BITS) - 1

    def __init__(self, voxel_size: float):
        self.voxel_size = voxel_size
        self._cells: dict[int, np.ndarray] = {}

    def _pack(self, points: np.ndarray) -> np.ndarray:
        idx = np.floor(points[:, :3] / self.voxel_size).astype(np.int64) + self._OFFSET
        idx = np.clip(idx, 0, self._MASK)
        return (idx[:, 0] << (2 * self._BITS)) | (idx[:, 1] << self._BITS) | idx[:, 2]

    def add(self, points: np.ndarray) -> None:
        if len(points) == 0:
            return
        keys = self._pack(points)
        unique_keys, inverse = np.unique(keys, return_inverse=True)
        sums = np.zeros((len(unique_keys), 6), dtype=np.float64)
        np.add.at(sums, inverse, points[:, :6])
        counts = np.bincount(inverse, minlength=len(unique_keys))

        for i, key in enumerate(unique_keys):
            key = int(key)
            cell = self._cells.get(key)
            if cell is None:
                self._cells[key] = np.append(sums[i], counts[i])
            else:
                cell[:6] += sums[i]
                cell[6] += counts[i]

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
        self.declare_parameter("secondary_camera_topic", "")  # e.g. /camera_head/...
        self.declare_parameter("voxel_size", 0.005)
        self.declare_parameter("roi_center", [0.35, 0.0, 0.06])
        self.declare_parameter("roi_radius", 0.15)
        self.declare_parameter("colour", "any")
        self.declare_parameter("remove_table", True)
        self.declare_parameter("table_z", 0.0)
        self.declare_parameter("table_margin", 0.01)
        self.declare_parameter("outlier_filter", True)
        self.declare_parameter("outlier_nb_neighbors", 20)
        self.declare_parameter("outlier_std_ratio", 2.0)
        self.declare_parameter("tf_fallback_latest", True)
        self.declare_parameter("max_tf_age_sec", 0.05)
        self.declare_parameter("save_path", "")
        self.declare_parameter("export_mesh", False)
        self.declare_parameter("save_metadata", True)

        self._camera_topic = self.get_parameter("camera_topic").value
        self._secondary_topic = str(self.get_parameter("secondary_camera_topic").value).strip()
        self._roi_center = np.array(self.get_parameter("roi_center").value, dtype=np.float32)
        self._roi_radius = float(self.get_parameter("roi_radius").value)
        self._colour = str(self.get_parameter("colour").value)
        self._remove_table = _as_bool(self.get_parameter("remove_table").value)
        self._outlier_filter = _as_bool(self.get_parameter("outlier_filter").value)
        self._outlier_k = int(self.get_parameter("outlier_nb_neighbors").value)
        self._outlier_std = float(self.get_parameter("outlier_std_ratio").value)
        self._tf_fallback_latest = _as_bool(self.get_parameter("tf_fallback_latest").value)
        self._max_tf_age = float(self.get_parameter("max_tf_age_sec").value)
        self._save_path = self.get_parameter("save_path").value
        self._export_mesh = _as_bool(self.get_parameter("export_mesh").value)
        self._save_metadata = _as_bool(self.get_parameter("save_metadata").value)

        self._voxels = VoxelMap(float(self.get_parameter("voxel_size").value))
        self._lock = threading.Lock()
        self._active = False
        self._frames_merged = 0
        self._frames_received = 0
        self._frames_empty_after_filter = 0
        self._frames_tf_failed = 0
        self._frames_outlier_emptied = 0
        self._view_az_hist = np.zeros(8, dtype=np.int64)  # occlusion coverage bins

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        self.create_subscription(
            PointCloud2, self._camera_topic, self._cloud_cb,
            rclpy.qos.QoSPresetProfiles.SENSOR_DATA.value,
        )
        if self._secondary_topic:
            self.create_subscription(
                PointCloud2, self._secondary_topic, self._cloud_cb,
                rclpy.qos.QoSPresetProfiles.SENSOR_DATA.value,
            )
        self.create_subscription(PoseStamped, "/ur_grasp/grasp_pose", self._grasp_pose_cb, 10)

        self._cloud_pub = self.create_publisher(
            PointCloud2, "/ur_perception/reconstructed_points", 10
        )

        self.create_service(Trigger, "/ur_perception/reconstruct/start", self._start_cb)
        self.create_service(Trigger, "/ur_perception/reconstruct/stop", self._stop_cb)

        self.create_timer(3.0, self._diagnostics_cb)

        self.get_logger().info(
            f"ObjectReconstructorNode ready — camera_topic={self._camera_topic}  "
            f"secondary={self._secondary_topic or '(none)'}  "
            f"roi_center={self._roi_center.tolist()}  roi_radius={self._roi_radius}  "
            f"colour={self._colour}  remove_table={self._remove_table}  "
            f"outlier_filter={self._outlier_filter}  export_mesh={self._export_mesh}"
        )

    def _grasp_pose_cb(self, msg: PoseStamped) -> None:
        p = msg.pose.position
        self._roi_center = np.array([p.x, p.y, p.z], dtype=np.float32)

    def _start_cb(self, _req, response):
        with self._lock:
            self._voxels.clear()
            self._frames_merged = 0
            self._frames_received = 0
            self._frames_empty_after_filter = 0
            self._frames_tf_failed = 0
            self._frames_outlier_emptied = 0
            self._view_az_hist[:] = 0
            self._active = True
        response.success = True
        response.message = "Reconstruction started — accumulating frames"
        self.get_logger().info(response.message)
        return response

    def _diagnostics_cb(self) -> None:
        with self._lock:
            active = self._active
            received = self._frames_received
            merged = self._frames_merged
            empty_after_filter = self._frames_empty_after_filter
            tf_failed = self._frames_tf_failed
            outlier_emptied = self._frames_outlier_emptied
            n_vox = len(self._voxels)
            az = self._view_az_hist.copy()
        if not active:
            return
        if received == 0:
            self.get_logger().warn(
                f"reconstruction active but no messages on "
                f"'{self._camera_topic}'"
                + (f" / '{self._secondary_topic}'" if self._secondary_topic else "")
                + " — is the camera publishing?"
            )
        elif merged == 0:
            self.get_logger().warn(
                f"{received} frame(s) received but 0 merged "
                f"(filter empties={empty_after_filter}, tf_fail={tf_failed}, "
                f"outlier_emptied={outlier_emptied}) — "
                f"roi_center={self._roi_center.tolist()} "
                f"roi_radius={self._roi_radius}m"
            )
        else:
            covered = int(np.count_nonzero(az))
            self.get_logger().info(
                f"reconstruction progress: {merged}/{received} frames, "
                f"{n_vox} voxels, azimuth_bins={covered}/8, tf_fail={tf_failed}"
            )

    def _stop_cb(self, _req, response):
        with self._lock:
            self._active = False
            n_points = len(self._voxels)
            n_frames = self._frames_merged
            cloud = self._voxels.as_array()
            az = self._view_az_hist.copy()
            received = self._frames_received
            outlier_emptied = self._frames_outlier_emptied

        save_path = self.get_parameter("save_path").value
        export_mesh = _as_bool(self.get_parameter("export_mesh").value)
        save_metadata = _as_bool(self.get_parameter("save_metadata").value)
        saved_msg = ""
        if save_path and n_points > 0:
            _write_ply(save_path, cloud)
            saved_msg = f", saved to {save_path}"
            if save_metadata:
                meta_path = _metadata_path_for(save_path)
                _write_metadata(meta_path, {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "n_voxels": int(n_points),
                    "n_frames_merged": int(n_frames),
                    "n_frames_received": int(received),
                    "n_frames_outlier_emptied": int(outlier_emptied),
                    "camera_topic": self._camera_topic,
                    "secondary_camera_topic": self._secondary_topic,
                    "voxel_size": float(self.get_parameter("voxel_size").value),
                    "roi_center": self._roi_center.tolist(),
                    "roi_radius": float(self._roi_radius),
                    "colour": str(self.get_parameter("colour").value),
                    "remove_table": _as_bool(self.get_parameter("remove_table").value),
                    "outlier_filter": _as_bool(self.get_parameter("outlier_filter").value),
                    "azimuth_bin_counts": az.tolist(),
                    "azimuth_bins_covered": int(np.count_nonzero(az)),
                    "save_path": save_path,
                })
                saved_msg += f", meta {meta_path}"
            if export_mesh:
                mesh_path = _mesh_path_for(save_path)
                if _try_write_mesh(mesh_path, cloud, self.get_logger()):
                    saved_msg += f", mesh to {mesh_path}"
                else:
                    saved_msg += ", mesh export skipped (open3d missing or failed)"

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

        with self._lock:
            self._frames_received += 1

        cloud = decode_pointcloud2(msg)
        if cloud is None:
            return

        cloud = self._transform_to_base(cloud, msg.header.frame_id, msg.header.stamp)
        if cloud is None:
            with self._lock:
                self._frames_tf_failed += 1
            return

        cloud = self._filter_cloud(cloud)
        if len(cloud) == 0:
            with self._lock:
                self._frames_empty_after_filter += 1
            return

        if _as_bool(self.get_parameter("outlier_filter").value):
            cloud = _statistical_outlier_filter(
                cloud,
                nb_neighbors=int(self.get_parameter("outlier_nb_neighbors").value),
                std_ratio=float(self.get_parameter("outlier_std_ratio").value),
            )
            if len(cloud) == 0:
                with self._lock:
                    self._frames_outlier_emptied += 1
                return

        with self._lock:
            self._voxels.add(cloud)
            self._frames_merged += 1
            self._update_azimuth_hist(cloud)
            fused = self._voxels.as_array()

        self._publish_cloud(fused)

    def _update_azimuth_hist(self, cloud: np.ndarray) -> None:
        """Track which azimuth sectors around roi_center have been observed."""
        dxy = cloud[:, :2] - self._roi_center[:2]
        ang = np.arctan2(dxy[:, 1], dxy[:, 0])  # [-pi, pi]
        bins = ((ang + np.pi) / (2 * np.pi) * 8).astype(np.int64) % 8
        for b in np.unique(bins):
            self._view_az_hist[int(b)] += int(np.count_nonzero(bins == b))

    def _filter_cloud(self, cloud: np.ndarray) -> np.ndarray:
        dist = np.linalg.norm(cloud[:, :3] - self._roi_center, axis=1)
        cloud = cloud[dist <= self._roi_radius]
        if len(cloud) == 0:
            return cloud

        colour = str(self.get_parameter("colour").value)
        if colour and colour != "any":
            rgb = cloud[:, 3:6]
            mask = colour_mask(np.clip(rgb, 0, 255).astype(np.uint8), colour)
            cloud = cloud[mask]
            if len(cloud) == 0:
                return cloud

        if _as_bool(self.get_parameter("remove_table").value):
            table_z = float(self.get_parameter("table_z").value)
            margin = float(self.get_parameter("table_margin").value)
            cloud = cloud[cloud[:, 2] > (table_z + margin)]

        return cloud

    def _transform_to_base(
        self, cloud: np.ndarray, source_frame: str, stamp
    ) -> Optional[np.ndarray]:
        if source_frame == BASE_FRAME:
            return cloud

        # Prefer stamped TF so fast arm motion does not smear the fusion. The
        # stamped lookup gives the *exact* camera pose at capture time; the
        # Time()-latest fallback below is only an approximation (whatever the
        # buffer holds "now") and smears the reconstruction along the arm's
        # motion direction whenever "now" has drifted from the capture
        # instant — verified live: a 5cm cube came out visibly elongated with
        # a 0.05s primary timeout / 0.25s max age, because most frames fell
        # back to the approximation. Widening the primary timeout lets far
        # more frames use the exact lookup instead.
        transform = None
        try:
            transform = self._tf_buffer.lookup_transform(
                BASE_FRAME, source_frame, stamp,
                timeout=rclpy.duration.Duration(seconds=0.2),
            )
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException):
            if not self._tf_fallback_latest:
                return None
            try:
                transform = self._tf_buffer.lookup_transform(
                    BASE_FRAME, source_frame, Time(),
                    timeout=rclpy.duration.Duration(seconds=0.1),
                )
                # Drop if the stamp is too old relative to "now" (arm moved a lot).
                age = (self.get_clock().now() - Time.from_msg(stamp)).nanoseconds * 1e-9
                if age > self._max_tf_age:
                    self.get_logger().warn(
                        f"TF stamp age {age:.3f}s > max_tf_age_sec={self._max_tf_age} "
                        f"— dropping frame to avoid smear",
                        throttle_duration_sec=2.0,
                    )
                    return None
            except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                    tf2_ros.ExtrapolationException) as e:
                self.get_logger().warn(
                    f"TF {source_frame}->{BASE_FRAME} failed: {e}",
                    throttle_duration_sec=2.0,
                )
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
    with open(path, "w") as f:
        f.write("ply\nformat ascii 1.0\n")
        f.write(f"element vertex {len(cloud)}\n")
        f.write("property float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        f.write("end_header\n")
        for x, y, z, r, g, b in cloud:
            f.write(f"{x} {y} {z} {int(r)} {int(g)} {int(b)}\n")


def _mesh_path_for(save_path: str) -> str:
    root, ext = os.path.splitext(save_path)
    if ext.lower() == ".ply":
        return f"{root}.mesh.ply"
    return f"{save_path}.mesh.ply"


def _metadata_path_for(save_path: str) -> str:
    root, ext = os.path.splitext(save_path)
    if ext.lower() == ".ply":
        return f"{root}.json"
    return f"{save_path}.json"


def _write_metadata(path: str, meta: dict) -> None:
    with open(path, "w") as f:
        json.dump(meta, f, indent=2)


def _try_write_mesh(path: str, cloud: np.ndarray, logger) -> bool:
    try:
        import open3d as o3d
    except ImportError:
        logger.warn("export_mesh=true but open3d is not installed — pip install open3d")
        return False

    if len(cloud) < 50:
        logger.warn(f"Too few points ({len(cloud)}) for mesh export")
        return False

    try:
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(cloud[:, :3].astype(np.float64))
        colors = np.clip(cloud[:, 3:6] / 255.0, 0.0, 1.0).astype(np.float64)
        pcd.colors = o3d.utility.Vector3dVector(colors)
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=0.02, max_nn=30)
        )
        pcd.orient_normals_consistent_tangent_plane(30)
        mesh, _densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
            pcd, depth=8
        )
        bbox = pcd.get_axis_aligned_bounding_box()
        mesh = mesh.crop(bbox)
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_non_manifold_edges()
        o3d.io.write_triangle_mesh(path, mesh)
        return True
    except Exception as exc:
        logger.warn(f"Mesh export failed: {exc}")
        return False


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
