#!/usr/bin/env python3
"""
grasp_node.py — Grasp detection node for UR3 + Robotiq 2F-85.

Two backends (auto-selected at startup):
  PRIMARY   → simple_grasping  (ros-humble-simple-grasping)
              Calls the FindGraspableObjects action server.
              Returns moveit_msgs/Grasp[] with full pre/post trajectories.
  FALLBACK  → ur_grasp/CylinderGraspDetector (numpy, no extra deps)
              Colour + centroid-based estimation from raw PointCloud2.

Publishes
─────────
  /ur_grasp/grasp_pose        geometry_msgs/PoseStamped  (best grasp, base_link frame)
  /ur_grasp/grasp_marker      visualization_msgs/MarkerArray  (RViz arrows)

Subscribes
──────────
  <camera_topic>          sensor_msgs/PointCloud2   (default /camera_wrist/depth/color/points)
  <reconstructed_topic>   sensor_msgs/PointCloud2   (optional, when use_reconstructed=true)

Services
────────
  /ur_grasp/detect   std_srvs/Trigger  → runs detection + publishes result
                     Response message contains x,y,z,confidence

Parameters
──────────
  colour             (str,   default "any")  target colour filter
  backend             (str,   default "auto") "simple_grasping" | "numpy" | "auto"
  min_confidence      (float, default 0.2)    discard candidates below this
  camera_topic        (str,   default "/camera_wrist/depth/color/points")
                       point cloud topic to detect from. Use
                       "/camera_head/depth/color/points" for the fixed
                       head-mounted camera instead.
  use_reconstructed   (bool,  default false)  prefer fused multi-view cloud from
                       object_reconstructor_node when it has points; fall back
                       to the live camera_topic cloud otherwise.
  reconstructed_topic (str,   default "/ur_perception/reconstructed_points")
  min_recon_points    (int,   default 200)    quality gate: ignore fused cloud
                       with fewer points than this (fall back to live)
  continuous_detect_hz (float, default 0.0)   if > 0, re-run detection on a
                       timer at this rate and keep /ur_grasp/grasp_pose
                       updated automatically — the useful mode when the
                       camera is wrist-mounted, since the object's apparent
                       position in the point cloud changes as the arm
                       approaches (this is what makes servo_node's PBVS loop
                       actually closed-loop against live perception instead
                       of a single frozen detection).

Usage
─────
  source install/setup.bash
  ros2 run ur_grasp grasp_node

  # trigger detection:
  ros2 service call /ur_grasp/detect std_srvs/srv/Trigger {}

  # set colour before detecting:
  ros2 param set /grasp_node colour red
  ros2 service call /ur_grasp/detect std_srvs/srv/Trigger {}
"""

import threading
from typing import Optional

import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

import tf2_ros
import tf2_geometry_msgs  # registers PoseStamped transforms

from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import PointCloud2
from std_srvs.srv import Trigger
from visualization_msgs.msg import Marker, MarkerArray


def _as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "on")
    return bool(value)


class GraspNode(Node):
    def __init__(self):
        super().__init__("grasp_node")

        # ── parameters ──────────────────────────────────────────────────────
        self.declare_parameter("colour",         "any")
        self.declare_parameter("backend",        "auto")
        self.declare_parameter("min_confidence", 0.20)
        self.declare_parameter("camera_topic",   "/camera_wrist/depth/color/points")
        self.declare_parameter("use_reconstructed", False)
        self.declare_parameter("reconstructed_topic", "/ur_perception/reconstructed_points")
        self.declare_parameter("min_recon_points", 200)
        self.declare_parameter("continuous_detect_hz", 0.0)

        self._colour     = self.get_parameter("colour").value
        self._backend    = self.get_parameter("backend").value
        self._min_conf   = self.get_parameter("min_confidence").value
        self._camera_topic = self.get_parameter("camera_topic").value
        self._use_reconstructed = _as_bool(self.get_parameter("use_reconstructed").value)
        self._reconstructed_topic = self.get_parameter("reconstructed_topic").value
        self._min_recon_points = int(self.get_parameter("min_recon_points").value)
        self._continuous_hz = float(self.get_parameter("continuous_detect_hz").value)

        # ── state ────────────────────────────────────────────────────────────
        self._latest_cloud: Optional[PointCloud2] = None
        self._latest_recon: Optional[PointCloud2] = None
        self._cloud_lock = threading.Lock()
        self._last_grasp: Optional[PoseStamped] = None

        # ── determine backend ────────────────────────────────────────────────
        self._use_simple_grasping = False
        if self._backend in ("auto", "simple_grasping"):
            try:
                from object_recognition_msgs.action import FindObjects  # noqa: F401
                self._use_simple_grasping = True
                self.get_logger().info("Backend: simple_grasping (FindObjects action)")
            except ImportError:
                if self._backend == "simple_grasping":
                    self.get_logger().error(
                        "simple_grasping backend requested but "
                        "object_recognition_msgs not found. "
                        "Run: sudo apt install ros-humble-simple-grasping"
                    )
                else:
                    self.get_logger().info("Backend: numpy centroid (simple_grasping not available)")

        if self._use_simple_grasping:
            from object_recognition_msgs.action import FindObjects
            self._find_objects_client = ActionClient(
                self, FindObjects, "/find_objects_with_grasps"
            )

        # ── TF ───────────────────────────────────────────────────────────────
        self._tf_buffer   = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        # ── pub / sub / srv ──────────────────────────────────────────────────
        self._cloud_sub = self.create_subscription(
            PointCloud2,
            self._camera_topic,
            self._cloud_cb,
            rclpy.qos.QoSPresetProfiles.SENSOR_DATA.value,
        )
        if self._use_reconstructed:
            self.create_subscription(
                PointCloud2,
                self._reconstructed_topic,
                self._recon_cb,
                10,
            )
        self._pose_pub = self.create_publisher(PoseStamped,    "/ur_grasp/grasp_pose",   10)
        self._marker_pub = self.create_publisher(MarkerArray,  "/ur_grasp/grasp_marker", 10)

        self._detect_srv = self.create_service(Trigger, "/ur_grasp/detect", self._detect_cb)

        self._continuous_timer = None
        if self._continuous_hz > 0.0:
            self._continuous_timer = self.create_timer(
                1.0 / self._continuous_hz, self._continuous_detect_cb
            )

        self.get_logger().info(
            f"GraspNode ready — colour={self._colour}  backend="
            f"{'simple_grasping' if self._use_simple_grasping else 'numpy'}  "
            f"camera_topic={self._camera_topic}  "
            f"use_reconstructed={self._use_reconstructed}  "
            f"min_recon_points={self._min_recon_points}  "
            f"continuous_detect_hz={self._continuous_hz}"
        )

    # ── callbacks ─────────────────────────────────────────────────────────────

    def _cloud_cb(self, msg: PointCloud2) -> None:
        with self._cloud_lock:
            self._latest_cloud = msg

    def _recon_cb(self, msg: PointCloud2) -> None:
        with self._cloud_lock:
            self._latest_recon = msg

    def _detect_cb(self, _req, response):
        """Trigger service — run detection and return summary."""
        self.get_logger().info("Detection requested...")

        grasp = self._run_detection()

        if grasp is None:
            response.success = False
            response.message = "No graspable object detected"
            self.get_logger().warn(response.message)
            return response

        px = grasp.pose.position
        response.success = True
        response.message = (
            f"Grasp detected at ({px.x:.3f}, {px.y:.3f}, {px.z:.3f}) "
            f"frame={grasp.header.frame_id}"
        )
        self.get_logger().info(response.message)
        return response

    def _continuous_detect_cb(self):
        """Timer callback — re-run detection and republish, no service response.

        This is what turns wrist-camera perception into an actual closed
        loop: the object's position in the point cloud shifts as the arm
        servos toward it, so grasp_pose needs to keep tracking that instead
        of being set once from the first frame.
        """
        self._run_detection(log_failures=False)

    def _run_detection(self, log_failures: bool = True) -> Optional[PoseStamped]:
        if self._use_simple_grasping:
            grasp = self._detect_simple_grasping()
        else:
            grasp = self._detect_numpy()

        if grasp is None:
            if log_failures:
                self.get_logger().warn("No graspable object detected")
            return None

        self._last_grasp = grasp
        self._pose_pub.publish(grasp)
        self._publish_marker(grasp)
        return grasp

    # ── backends ──────────────────────────────────────────────────────────────

    def _detect_numpy(self) -> Optional[PoseStamped]:
        """Colour-centroid grasp estimation (no external deps)."""
        from ur_grasp.cylinder_grasp_detector import decode_pointcloud2, estimate_cylinder_grasp

        with self._cloud_lock:
            recon_msg = self._latest_recon if self._use_reconstructed else None
            live_msg = self._latest_cloud

        # Prefer fused multi-view cloud when enabled, non-empty, and past the
        # quality gate; else live RGBD.
        cloud_msg = None
        source = "live"
        if (
            recon_msg is not None
            and recon_msg.width * recon_msg.height >= self._min_recon_points
        ):
            cloud_msg = recon_msg
            source = "reconstructed"
        elif recon_msg is not None and self._use_reconstructed:
            n = recon_msg.width * recon_msg.height
            self.get_logger().warn(
                f"Fused cloud has only {n} points (< min_recon_points="
                f"{self._min_recon_points}) — falling back to live camera"
            )
        if cloud_msg is None and live_msg is not None:
            cloud_msg = live_msg
            source = "live"

        if cloud_msg is None:
            self.get_logger().warn("No point cloud received yet.")
            return None

        cloud = decode_pointcloud2(cloud_msg)
        if cloud is None:
            self.get_logger().warn("Point cloud decoded to zero points.")
            return None

        # estimate_cylinder_grasp()'s Z/XY thresholds are base_link-frame
        # workspace bounds (table height, reach radius) — the cloud must be
        # transformed into base_link *before* filtering, not after picking a
        # candidate. Filtering camera-frame coordinates against those bounds
        # silently rejects every real point (camera Z is depth, not height).
        # Reconstructed clouds are already published in base_link.
        cloud = self._transform_cloud_to_base(cloud, cloud_msg.header.frame_id)
        if cloud is None:
            return None

        colour = self.get_parameter("colour").value
        candidate = estimate_cylinder_grasp(cloud, colour=colour)

        if candidate is None:
            return None
        if candidate.confidence < self._min_conf:
            self.get_logger().warn(
                f"Confidence {candidate.confidence:.2f} < threshold {self._min_conf}"
            )
            return None

        self.get_logger().info(
            f"[numpy/{source}] Grasp: ({candidate.x:.3f}, {candidate.y:.3f}, "
            f"grasp_z={candidate.grasp_z:.3f})  "
            f"h={candidate.object_height:.3f}m  "
            f"r={candidate.object_radius:.3f}m  "
            f"conf={candidate.confidence:.2f}  pts={candidate.n_points}"
        )

        return self._make_pose(candidate.x, candidate.y, candidate.grasp_z, "base_link")

    def _detect_simple_grasping(self) -> Optional[PoseStamped]:
        """Use simple_grasping FindObjects action server."""
        from object_recognition_msgs.action import FindObjects

        if not self._find_objects_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().warn("FindObjects server not available — falling back to numpy.")
            return self._detect_numpy()

        goal = FindObjects.Goal()
        event = threading.Event()
        result_holder = [None]

        def _done(future):
            result_holder[0] = future.result()
            event.set()

        send_future = self._find_objects_client.send_goal_async(goal)
        send_future.add_done_callback(lambda f: f.result().get_result_async().add_done_callback(_done))
        if not event.wait(timeout=15.0):
            self.get_logger().warn("FindObjects timed out — falling back to numpy.")
            return self._detect_numpy()

        result = result_holder[0]
        if result is None or not result.result.objects.objects:
            self.get_logger().info("simple_grasping found no objects — trying numpy.")
            return self._detect_numpy()

        # Pick the object with the most grasps (highest confidence)
        best_obj = max(result.result.objects.objects,
                       key=lambda o: len(o.grasps) if hasattr(o, 'grasps') else 0)
        grasps = result.result.grasps.grasps
        if not grasps:
            return self._detect_numpy()

        # Best grasp = first (simple_grasping ranks by quality)
        g = grasps[0]
        pose = PoseStamped()
        pose.header.frame_id = "base_link"
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose = g.grasp_pose.pose

        self.get_logger().info(
            f"[simple_grasping] Grasp at "
            f"({pose.pose.position.x:.3f}, {pose.pose.position.y:.3f}, "
            f"{pose.pose.position.z:.3f})  {len(grasps)} candidates"
        )
        return pose

    # ── helpers ───────────────────────────────────────────────────────────────

    def _transform_cloud_to_base(self, cloud, source_frame: str):
        """Transform an (N,6) [x,y,z,r,g,b] cloud's XYZ columns into base_link."""
        if source_frame == "base_link":
            return cloud
        try:
            transform = self._tf_buffer.lookup_transform(
                "base_link", source_frame,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.5),
            )
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f"TF {source_frame}->base_link failed: {e}")
            return None

        q = transform.transform.rotation
        t = transform.transform.translation
        x2, y2, z2, w2 = q.x * q.x, q.y * q.y, q.z * q.z, q.w * q.w
        R = np.array([
            [x2 - y2 - z2 + w2,       2 * (q.x * q.y - q.z * q.w), 2 * (q.x * q.z + q.y * q.w)],
            [2 * (q.x * q.y + q.z * q.w), -x2 + y2 - z2 + w2,      2 * (q.y * q.z - q.x * q.w)],
            [2 * (q.x * q.z - q.y * q.w), 2 * (q.y * q.z + q.x * q.w), -x2 - y2 + z2 + w2],
        ])
        translation = np.array([t.x, t.y, t.z])

        transformed = cloud.copy()
        transformed[:, :3] = cloud[:, :3] @ R.T + translation
        return transformed

    def _transform_to_base(self, pose: PoseStamped) -> Optional[PoseStamped]:
        if pose.header.frame_id == "base_link":
            return pose
        try:
            transform = self._tf_buffer.lookup_transform(
                "base_link",
                pose.header.frame_id,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.5),
            )
            return tf2_geometry_msgs.do_transform_pose_stamped(pose, transform)
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            self.get_logger().warn(f"TF {pose.header.frame_id}->base_link failed: {e}")
            return None

    def _make_pose(self, x: float, y: float, z: float, frame: str) -> PoseStamped:
        pose = PoseStamped()
        pose.header.frame_id = frame
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        # Downward grasp orientation
        pose.pose.orientation.x = 1.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 0.0
        return pose

    def _publish_marker(self, pose: PoseStamped) -> None:
        """Publish an arrow marker in RViz at the grasp pose."""
        arr = MarkerArray()
        m = Marker()
        m.header = pose.header
        m.ns = "grasp"
        m.id = 0
        m.type = Marker.ARROW
        m.action = Marker.ADD
        m.pose = pose.pose
        m.scale.x = 0.08
        m.scale.y = 0.015
        m.scale.z = 0.015
        m.color.r = 1.0
        m.color.g = 0.5
        m.color.a = 1.0
        arr.markers.append(m)
        # Sphere at contact point
        s = Marker()
        s.header = pose.header
        s.ns = "grasp"
        s.id = 1
        s.type = Marker.SPHERE
        s.action = Marker.ADD
        s.pose = pose.pose
        s.scale.x = s.scale.y = s.scale.z = 0.03
        s.color.r = 1.0
        s.color.g = 0.2
        s.color.a = 0.9
        arr.markers.append(s)
        self._marker_pub.publish(arr)


def main(args=None):
    rclpy.init(args=args)
    node = GraspNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
