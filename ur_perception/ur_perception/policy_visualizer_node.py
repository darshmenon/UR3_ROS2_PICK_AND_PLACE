#!/usr/bin/env python3
"""
PolicyVisualizerNode - Dual-view (head + wrist) composite with a grasp
probability heatmap, for watching what a brain (RL/OpenVLA/flow policy) has
to work with.

Subscribes to:
  <head_color_topic>    (sensor_msgs/Image)         default /camera_head/color/image_raw
  <wrist_color_topic>   (sensor_msgs/Image)          default /camera_wrist/color/image_raw
  <camera_info_topic>   (sensor_msgs/CameraInfo)  [once]  default /camera_head/camera_info
  /detected_objects      (ur_interfaces/msg/DetectedObjectArray)

Publishes:
  /policy_visualizer/composite_image   (sensor_msgs/Image)  side-by-side BGR image:
    [ head view + confidence heatmap | wrist (close-up) view ]

The heatmap is seeded from object_detector_node's published detections
(3-D position in base_link + confidence) rather than any policy's internal
attention — this keeps the visualizer decoupled from whichever brain
(RL / OpenVLA / flow) happens to be running.
"""

import threading
from typing import Optional

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy

import tf2_ros
import tf2_geometry_msgs  # registers PoseStamped transforms
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import CameraInfo, Image

try:
    from ur_interfaces.msg import DetectedObjectArray
    DETECTED_OBJECT_ARRAY_AVAILABLE = True
except ImportError:
    DETECTED_OBJECT_ARRAY_AVAILABLE = False


_SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)

_CAM_INFO_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
    durability=QoSDurabilityPolicy.VOLATILE,
)

_HEATMAP_SIGMA_PX = 28.0
_HEATMAP_ALPHA = 0.45


class PolicyVisualizerNode(Node):
    """Composites head + wrist camera views with a detection-confidence heatmap."""

    def __init__(self) -> None:
        super().__init__('policy_visualizer_node')

        self.declare_parameter('head_color_topic', '/camera_head/color/image_raw')
        self.declare_parameter('wrist_color_topic', '/camera_wrist/color/image_raw')
        self.declare_parameter('camera_info_topic', '/camera_head/camera_info')
        # NOTE: gz-sim publishes image/depth data using the *native* (non-rotated)
        # link frame, not the ROS-standard "_optical_frame" convention — same
        # gotcha documented in intel_rgbd_cam_d435.urdf.xacro for the point cloud,
        # and why DepthPoseEstimator.estimate_object_pose() tags its pinhole-math
        # poses with frame_id='camera_head_link' rather than the optical frame.
        self.declare_parameter('camera_frame', 'camera_head_link')
        self.declare_parameter('base_frame', 'base_link')

        head_topic = self.get_parameter('head_color_topic').value
        wrist_topic = self.get_parameter('wrist_color_topic').value
        cam_info_topic = self.get_parameter('camera_info_topic').value
        self._camera_frame = self.get_parameter('camera_frame').value
        self._base_frame = self.get_parameter('base_frame').value

        if not DETECTED_OBJECT_ARRAY_AVAILABLE:
            self.get_logger().warn(
                'ur_interfaces/DetectedObjectArray not importable — heatmap will stay empty.'
            )

        self._bridge = CvBridge()
        self._lock = threading.Lock()
        self._latest_head: Optional[np.ndarray] = None
        self._latest_wrist: Optional[np.ndarray] = None
        self._latest_detections = []  # list of (x, y, z, confidence) in base_frame

        self._camera_info: Optional[CameraInfo] = None
        self._fx = self._fy = self._cx = self._cy = None

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        self.create_subscription(Image, head_topic, self._head_cb, _SENSOR_QOS)
        self.create_subscription(Image, wrist_topic, self._wrist_cb, _SENSOR_QOS)
        self._cam_info_sub = self.create_subscription(
            CameraInfo, cam_info_topic, self._cam_info_cb, _CAM_INFO_QOS
        )
        if DETECTED_OBJECT_ARRAY_AVAILABLE:
            self.create_subscription(
                DetectedObjectArray, '/detected_objects', self._detections_cb, 10
            )

        self._pub = self.create_publisher(Image, '/policy_visualizer/composite_image', 10)
        self.create_timer(1.0 / 10.0, self._compose)

        self.get_logger().info(
            f'PolicyVisualizerNode ready. head={head_topic} wrist={wrist_topic} '
            f'-> /policy_visualizer/composite_image'
        )

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #

    def _head_cb(self, msg: Image) -> None:
        try:
            img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            with self._lock:
                self._latest_head = img
        except CvBridgeError as e:
            self.get_logger().warn(f'Head image conversion failed: {e}', throttle_duration_sec=5.0)

    def _wrist_cb(self, msg: Image) -> None:
        try:
            img = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            with self._lock:
                self._latest_wrist = img
        except CvBridgeError as e:
            self.get_logger().warn(f'Wrist image conversion failed: {e}', throttle_duration_sec=5.0)

    def _cam_info_cb(self, msg: CameraInfo) -> None:
        if self._camera_info is not None:
            return
        self._camera_info = msg
        K = msg.k
        self._fx, self._fy = K[0], K[4]
        self._cx, self._cy = K[2], K[5]
        self.get_logger().info(
            f'Camera intrinsics received: fx={self._fx:.1f} fy={self._fy:.1f} '
            f'cx={self._cx:.1f} cy={self._cy:.1f}'
        )
        self.destroy_subscription(self._cam_info_sub)

    def _detections_cb(self, msg) -> None:
        detections = [
            (obj.position.x, obj.position.y, obj.position.z, float(obj.confidence))
            for obj in msg.objects
        ]
        with self._lock:
            self._latest_detections = detections

    # ------------------------------------------------------------------ #
    # TF + projection helpers
    # ------------------------------------------------------------------ #

    def _project_to_pixel(self, x: float, y: float, z: float) -> Optional[tuple]:
        """Transforms a base_frame point into the camera optical frame and
        pinhole-projects it to pixel coordinates. Returns None on failure or
        if the point is behind the camera."""
        pose = PoseStamped()
        pose.header.frame_id = self._base_frame
        pose.header.stamp = rclpy.time.Time().to_msg()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.w = 1.0

        try:
            transform = self._tf_buffer.lookup_transform(
                self._camera_frame,
                self._base_frame,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.1),
            )
            transformed = tf2_geometry_msgs.do_transform_pose_stamped(pose, transform)
        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException,
        ) as e:
            self.get_logger().warn(f'TF lookup to {self._camera_frame} failed: {e}', throttle_duration_sec=5.0)
            return None

        cx_cam = transformed.pose.position.x
        cy_cam = transformed.pose.position.y
        cz_cam = transformed.pose.position.z
        if cz_cam <= 0.01:
            return None  # behind or at the camera

        u = self._fx * (cx_cam / cz_cam) + self._cx
        v = self._fy * (cy_cam / cz_cam) + self._cy
        return u, v

    # ------------------------------------------------------------------ #
    # Compositing
    # ------------------------------------------------------------------ #

    def _draw_heatmap(self, image: np.ndarray, detections) -> np.ndarray:
        h, w = image.shape[:2]
        heat = np.zeros((h, w), dtype=np.float32)

        for x, y, z, confidence in detections:
            pixel = self._project_to_pixel(x, y, z)
            if pixel is None:
                continue
            u, v = pixel
            if not (0 <= u < w and 0 <= v < h):
                continue
            yy, xx = np.mgrid[0:h, 0:w]
            heat += confidence * np.exp(
                -(((xx - u) ** 2 + (yy - v) ** 2) / (2 * _HEATMAP_SIGMA_PX ** 2))
            )

        if heat.max() <= 1e-6:
            return image

        heat_norm = np.clip(heat / max(heat.max(), 1.0), 0.0, 1.0)
        heat_u8 = (heat_norm * 255).astype(np.uint8)
        heat_color = cv2.applyColorMap(heat_u8, cv2.COLORMAP_JET)

        mask = heat_norm[..., None]
        return (image * (1 - _HEATMAP_ALPHA * mask) + heat_color * (_HEATMAP_ALPHA * mask)).astype(np.uint8)

    def _compose(self) -> None:
        with self._lock:
            head = self._latest_head
            wrist = self._latest_wrist
            detections = list(self._latest_detections)

        if head is None or wrist is None:
            return

        if self._camera_info is not None:
            head_vis = self._draw_heatmap(head.copy(), detections)
        else:
            head_vis = head.copy()

        if wrist.shape[0] != head_vis.shape[0]:
            scale = head_vis.shape[0] / wrist.shape[0]
            wrist = cv2.resize(wrist, (int(wrist.shape[1] * scale), head_vis.shape[0]))

        composite = cv2.hconcat([head_vis, wrist])

        try:
            msg = self._bridge.cv2_to_imgmsg(composite, encoding='bgr8')
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = self._camera_frame
            self._pub.publish(msg)
        except CvBridgeError as e:
            self.get_logger().warn(f'Publish failed: {e}', throttle_duration_sec=5.0)


def main(args=None):
    rclpy.init(args=args)
    node = PolicyVisualizerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
