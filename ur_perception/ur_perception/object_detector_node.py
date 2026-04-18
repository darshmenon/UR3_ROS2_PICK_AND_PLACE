#!/usr/bin/env python3
"""
ObjectDetectorNode - Color + optional YOLO hybrid perception node.

Subscribes to:
  /camera_head/color/image_raw          (sensor_msgs/Image)
  /camera_head/depth/image_rect_raw     (sensor_msgs/Image)
  /camera_head/camera_info              (sensor_msgs/CameraInfo)  [latched, once]

Publishes:
  /detected_objects    (ur_interfaces/msg/DetectedObjectArray)
  /detection_image     (sensor_msgs/Image)  annotated BGR image
  /planning_scene      (moveit_msgs/msg/PlanningScene)

Parameters:
  use_yolo               (bool,  default False)
  confidence_threshold   (float, default 0.5)
  publish_planning_scene (bool,  default True)
  min_depth_m            (float, default 0.1)
  max_depth_m            (float, default 2.0)
"""

import sys
import threading
from typing import List, Optional, Dict, Any

import cv2
import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy, QoSDurabilityPolicy

import message_filters
from cv_bridge import CvBridge, CvBridgeError

from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped, TransformStamped
from std_msgs.msg import Header
from shape_msgs.msg import SolidPrimitive
from moveit_msgs.msg import PlanningScene, CollisionObject

import tf2_ros
import tf2_geometry_msgs  # registers PoseStamped transforms

from ur_perception.color_detector import ColorDetector
from ur_perception.depth_pose_estimator import DepthPoseEstimator

# Optional YOLO import - graceful fallback
_YOLO_AVAILABLE = False
try:
    from ultralytics import YOLO as _YOLO
    _YOLO_AVAILABLE = True
except ImportError:
    pass

# Cylinder dimensions for planning scene collision objects
_CYLINDER_HEIGHT = 0.15   # metres
_CYLINDER_RADIUS = 0.04   # metres

# QoS for image topics (sensor data - best effort)
_SENSOR_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.BEST_EFFORT,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
)

# QoS for CameraInfo — must be VOLATILE to match ros_gz_bridge publisher
_CAM_INFO_QOS = QoSProfile(
    reliability=QoSReliabilityPolicy.RELIABLE,
    history=QoSHistoryPolicy.KEEP_LAST,
    depth=1,
    durability=QoSDurabilityPolicy.VOLATILE,
)


class ObjectDetectorNode(Node):
    """Hybrid color + YOLO object detector publishing 3-D poses and planning scene objects."""

    def __init__(self) -> None:
        super().__init__('object_detector_node')

        # ------------------------------------------------------------------ #
        # Parameters
        # ------------------------------------------------------------------ #
        self.declare_parameter('use_yolo',               False)
        self.declare_parameter('confidence_threshold',   0.5)
        self.declare_parameter('publish_planning_scene', True)
        self.declare_parameter('min_depth_m',            0.1)
        self.declare_parameter('max_depth_m',            2.0)
        self.declare_parameter('target_colors',          ['red', 'green', 'blue', 'yellow', 'orange'])

        self._use_yolo               = self.get_parameter('use_yolo').value
        self._conf_thresh            = self.get_parameter('confidence_threshold').value
        self._pub_planning_scene     = self.get_parameter('publish_planning_scene').value
        self._min_depth_m            = self.get_parameter('min_depth_m').value
        self._max_depth_m            = self.get_parameter('max_depth_m').value
        self._target_colors: List[str] = list(self.get_parameter('target_colors').value)

        self.get_logger().info(
            f"Parameters: use_yolo={self._use_yolo}, "
            f"conf_thresh={self._conf_thresh:.2f}, "
            f"target_colors={self._target_colors}"
        )

        # ------------------------------------------------------------------ #
        # Internal state
        # ------------------------------------------------------------------ #
        self._bridge = CvBridge()
        self._camera_info: Optional[CameraInfo] = None
        self._depth_estimator: Optional[DepthPoseEstimator] = None
        self._info_lock = threading.Lock()

        # ------------------------------------------------------------------ #
        # Color detector
        # ------------------------------------------------------------------ #
        self._color_detector = ColorDetector(
            target_colors=self._target_colors,
            min_area=500,
        )

        # ------------------------------------------------------------------ #
        # Optional YOLO model
        # ------------------------------------------------------------------ #
        self._yolo_model = None
        if self._use_yolo:
            if _YOLO_AVAILABLE:
                try:
                    self._yolo_model = _YOLO('yolov8n.pt')
                    self.get_logger().info("YOLO model loaded (yolov8n.pt).")
                except Exception as exc:
                    self.get_logger().warn(f"Failed to load YOLO model: {exc}. Falling back to color only.")
                    self._yolo_model = None
            else:
                self.get_logger().warn(
                    "'ultralytics' not installed. use_yolo=True has no effect. "
                    "Install with: pip install ultralytics"
                )

        # ------------------------------------------------------------------ #
        # TF2
        # ------------------------------------------------------------------ #
        self._tf_buffer   = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        # ------------------------------------------------------------------ #
        # Publishers
        # ------------------------------------------------------------------ #
        self._pub_detected_objects = self.create_publisher(
            # ur_interfaces must be importable at runtime
            self._import_detected_object_array(),
            '/detected_objects',
            10,
        )

        self._pub_debug_image = self.create_publisher(
            Image,
            '/detection_image',
            QoSProfile(
                reliability=QoSReliabilityPolicy.BEST_EFFORT,
                history=QoSHistoryPolicy.KEEP_LAST,
                depth=1,
            ),
        )

        self._pub_planning_scene_pub = self.create_publisher(
            PlanningScene,
            '/planning_scene',
            QoSProfile(
                reliability=QoSReliabilityPolicy.RELIABLE,
                history=QoSHistoryPolicy.KEEP_LAST,
                depth=5,
            ),
        )

        # ------------------------------------------------------------------ #
        # Camera info subscription (once)
        # ------------------------------------------------------------------ #
        self._cam_info_sub = self.create_subscription(
            CameraInfo,
            '/camera_head/camera_info',
            self._cam_info_cb,
            _CAM_INFO_QOS,
        )

        # ------------------------------------------------------------------ #
        # Synchronised image subscriptions
        # ------------------------------------------------------------------ #
        self._color_sub = message_filters.Subscriber(
            self, Image, '/camera_head/color/image_raw', qos_profile=_SENSOR_QOS,
        )
        self._depth_sub = message_filters.Subscriber(
            self, Image, '/camera_head/depth/image_rect_raw', qos_profile=_SENSOR_QOS,
        )

        self._sync = message_filters.ApproximateTimeSynchronizer(
            [self._color_sub, self._depth_sub],
            queue_size=5,
            slop=0.05,
        )
        self._sync.registerCallback(self._image_cb)

        self.get_logger().info("ObjectDetectorNode started and waiting for camera data.")

    # ------------------------------------------------------------------ #
    # Helpers: dynamic message import
    # ------------------------------------------------------------------ #

    def _import_detected_object_array(self):
        """Import ur_interfaces DetectedObjectArray, with a graceful fallback."""
        try:
            from ur_interfaces.msg import DetectedObjectArray
            self._DetectedObject = __import__(
                'ur_interfaces.msg', fromlist=['DetectedObject']
            ).DetectedObject
            self._DetectedObjectArray = DetectedObjectArray
            self.get_logger().info("ur_interfaces messages imported successfully.")
            return DetectedObjectArray
        except ImportError:
            self.get_logger().warn(
                "ur_interfaces not found. /detected_objects will publish std_msgs/String as placeholder."
            )
            from std_msgs.msg import String
            self._DetectedObject = None
            self._DetectedObjectArray = None
            return String

    # ------------------------------------------------------------------ #
    # Callbacks
    # ------------------------------------------------------------------ #

    def _cam_info_cb(self, msg: CameraInfo) -> None:
        """Store camera intrinsics once."""
        with self._info_lock:
            if self._camera_info is not None:
                return  # already have it

            self._camera_info = msg
            K = msg.k  # row-major 3x3
            fx, fy = K[0], K[4]
            cx, cy = K[2], K[5]

            self._depth_estimator = DepthPoseEstimator(
                fx=fx, fy=fy, cx=cx, cy=cy,
                depth_scale=1.0,   # Ignition Gazebo depth camera publishes float32 metres
                patch_radius=5,
            )
            self.get_logger().info(
                f"Camera intrinsics received: fx={fx:.1f} fy={fy:.1f} cx={cx:.1f} cy={cy:.1f}"
            )
            # Unsubscribe from camera_info — we only need it once
            self.destroy_subscription(self._cam_info_sub)

    def _image_cb(self, color_msg: Image, depth_msg: Image) -> None:
        """Main perception callback — called for every synchronised image pair."""
        with self._info_lock:
            if self._depth_estimator is None:
                self.get_logger().warn(
                    "Camera info not yet received. Skipping frame.",
                    throttle_duration_sec=5.0,
                )
                return
            depth_estimator = self._depth_estimator

        # Convert ROS images to OpenCV / numpy
        try:
            bgr_image   = self._bridge.imgmsg_to_cv2(color_msg, desired_encoding='bgr8')
            depth_image = self._bridge.imgmsg_to_cv2(depth_msg, desired_encoding='passthrough')
        except CvBridgeError as e:
            self.get_logger().error(f"cv_bridge conversion failed: {e}")
            return

        stamp = color_msg.header.stamp

        # ------------------------------------------------------------------ #
        # Color detection
        # ------------------------------------------------------------------ #
        color_detections: List[Dict[str, Any]] = self._color_detector.detect(bgr_image)

        # ------------------------------------------------------------------ #
        # Optional YOLO detection
        # ------------------------------------------------------------------ #
        yolo_detections: List[Dict[str, Any]] = []
        if self._yolo_model is not None:
            yolo_detections = self._run_yolo(bgr_image)

        # Merge detections — color first, then YOLO appended
        all_detections = color_detections + yolo_detections

        # Filter by confidence
        all_detections = [
            d for d in all_detections if d['confidence'] >= self._conf_thresh
        ]

        # ------------------------------------------------------------------ #
        # 3-D pose estimation + TF transform
        # ------------------------------------------------------------------ #
        objects_3d = []   # list of (detection_dict, PoseStamped in base_link)
        for det in all_detections:
            pose_cam = depth_estimator.estimate_object_pose(
                centroid_px=det['centroid_px'],
                bbox=det['bbox'],
                depth_image=depth_image,
                label=det['label'],
                frame_id=color_msg.header.frame_id,
                stamp=stamp,
                min_depth_m=self._min_depth_m,
                max_depth_m=self._max_depth_m,
            )
            if pose_cam is None:
                continue

            pose_base = self._transform_pose(pose_cam, target_frame='base_link', stamp=stamp)
            if pose_base is None:
                continue

            objects_3d.append((det, pose_base))

        # ------------------------------------------------------------------ #
        # Publish DetectedObjectArray
        # ------------------------------------------------------------------ #
        self._publish_detected_objects(objects_3d, stamp)

        # ------------------------------------------------------------------ #
        # Publish planning scene
        # ------------------------------------------------------------------ #
        if self._pub_planning_scene and objects_3d:
            self._publish_planning_scene(objects_3d, stamp)

        # ------------------------------------------------------------------ #
        # Publish annotated debug image
        # ------------------------------------------------------------------ #
        vis = self._color_detector.draw_detections(bgr_image, all_detections)
        self._draw_yolo_detections(vis, yolo_detections)
        try:
            debug_msg = self._bridge.cv2_to_imgmsg(vis, encoding='bgr8')
            debug_msg.header.stamp = stamp
            debug_msg.header.frame_id = 'camera_head_link'
            self._pub_debug_image.publish(debug_msg)
        except CvBridgeError as e:
            self.get_logger().error(f"Failed to publish debug image: {e}")

    # ------------------------------------------------------------------ #
    # YOLO helpers
    # ------------------------------------------------------------------ #

    def _run_yolo(self, bgr_image: np.ndarray) -> List[Dict[str, Any]]:
        """Run YOLO inference and return detections in the same dict format as ColorDetector."""
        detections = []
        try:
            results = self._yolo_model(bgr_image, verbose=False)
            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    cls_name = self._yolo_model.names.get(cls_id, str(cls_id))
                    x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                    w = x2 - x1
                    h = y2 - y1
                    cx = x1 + w // 2
                    cy = y1 + h // 2
                    detections.append({
                        'label':       cls_name,
                        'bbox':        (x1, y1, w, h),
                        'centroid_px': (cx, cy),
                        'confidence':  conf,
                        'color_rgb':   (0.5, 0.5, 0.5),
                        'mask':        None,
                        'source':      'yolo',
                    })
        except Exception as e:
            self.get_logger().warn(f"YOLO inference error: {e}", throttle_duration_sec=5.0)
        return detections

    def _draw_yolo_detections(self, vis: np.ndarray, detections: List[Dict[str, Any]]) -> None:
        """Overlay YOLO bounding boxes on the visualisation image (in-place)."""
        for det in detections:
            x, y, w, h = det['bbox']
            label = det['label']
            conf  = det['confidence']
            cv2.rectangle(vis, (x, y), (x + w, y + h), (180, 180, 180), 2)
            cv2.putText(
                vis, f"YOLO:{label} {conf:.2f}", (x, max(0, y - 6)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1, cv2.LINE_AA,
            )

    # ------------------------------------------------------------------ #
    # TF helper
    # ------------------------------------------------------------------ #

    def _transform_pose(
        self,
        pose_stamped: PoseStamped,
        target_frame: str,
        stamp,
    ) -> Optional[PoseStamped]:
        """Transform a PoseStamped to target_frame. Returns None on failure."""
        try:
            transform = self._tf_buffer.lookup_transform(
                target_frame,
                pose_stamped.header.frame_id,
                rclpy.time.Time(),   # use latest available
                timeout=rclpy.duration.Duration(seconds=0.1),
            )
            transformed = tf2_geometry_msgs.do_transform_pose_stamped(pose_stamped, transform)
            return transformed
        except (
            tf2_ros.LookupException,
            tf2_ros.ConnectivityException,
            tf2_ros.ExtrapolationException,
        ) as e:
            self.get_logger().warn(
                f"TF lookup {pose_stamped.header.frame_id} -> {target_frame} failed: {e}",
                throttle_duration_sec=5.0,
            )
            return None

    # ------------------------------------------------------------------ #
    # Publishers
    # ------------------------------------------------------------------ #

    def _publish_detected_objects(self, objects_3d, stamp) -> None:
        """Build and publish a DetectedObjectArray (or String placeholder)."""
        if self._DetectedObjectArray is None:
            from std_msgs.msg import String
            msg = String()
            msg.data = f"{len(objects_3d)} objects detected"
            self._pub_detected_objects.publish(msg)
            return

        from ur_interfaces.msg import DetectedObjectArray, DetectedObject

        array_msg = DetectedObjectArray()
        array_msg.header.stamp = stamp
        array_msg.header.frame_id = 'base_link'

        for idx, (det, pose_base) in enumerate(objects_3d):
            obj = DetectedObject()
            obj.id = f"{det['label']}_{idx}"
            obj.label = det['label']
            obj.confidence = float(det['confidence'])

            # position — matches geometry_msgs/Point in DetectedObject.msg
            obj.position.x = pose_base.pose.position.x
            obj.position.y = pose_base.pose.position.y
            obj.position.z = pose_base.pose.position.z

            # dimensions — approximate from cylinder model (x=length, y=width, z=height)
            obj.dimensions.x = _CYLINDER_RADIUS * 2.0
            obj.dimensions.y = _CYLINDER_RADIUS * 2.0
            obj.dimensions.z = _CYLINDER_HEIGHT

            array_msg.objects.append(obj)

        self._pub_detected_objects.publish(array_msg)

    def _publish_planning_scene(self, objects_3d, stamp) -> None:
        """Publish all detected objects as cylinder CollisionObjects to MoveIt."""
        scene_msg = PlanningScene()
        scene_msg.is_diff = True

        for idx, (det, pose_base) in enumerate(objects_3d):
            co = CollisionObject()
            co.id = f"{det['label']}_{idx}"
            co.header.frame_id = 'base_link'
            co.header.stamp = stamp
            co.operation = CollisionObject.ADD

            primitive = SolidPrimitive()
            primitive.type = SolidPrimitive.CYLINDER
            # CYLINDER dimensions: [height, radius]
            primitive.dimensions = [_CYLINDER_HEIGHT, _CYLINDER_RADIUS]

            co.primitives.append(primitive)
            co.primitive_poses.append(pose_base.pose)

            scene_msg.world.collision_objects.append(co)

        self._pub_planning_scene_pub.publish(scene_msg)
        self.get_logger().debug(
            f"Published planning scene with {len(objects_3d)} collision object(s)."
        )


# ---------------------------------------------------------------------- #
# Utility
# ---------------------------------------------------------------------- #

def _safe_set(obj, field: str, value) -> None:
    """Set an attribute on a ROS message only if it exists — avoids AttributeError on unknown fields."""
    if hasattr(obj, field):
        try:
            setattr(obj, field, value)
        except Exception:
            pass


# ---------------------------------------------------------------------- #
# Entry point
# ---------------------------------------------------------------------- #

def main(args=None) -> None:
    rclpy.init(args=args)
    node = ObjectDetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.get_logger().info("ObjectDetectorNode shutting down.")
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
