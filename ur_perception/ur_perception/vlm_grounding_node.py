#!/usr/bin/env python3
"""
Open-vocabulary object grounding with a local VLM (Ollama, default qwen2.5vl:3b).

Send a text query such as "the red cylinder" on /vlm/query. The node asks the VLM for the object's
bounding box in the latest colour image, reads the depth at the box centre, back-projects it to a 3D
pose in base_link and publishes it. The 3B model's boxes are loose (about 2x too big), so the id is
chosen by which /detected_objects entry projects inside the box (nearest to the box centre if several):

    /vlm/target_pose       geometry_msgs/PoseStamped   pose of the grounded object in base_link
    /vlm/target_object_id  std_msgs/String             id of the nearest /detected_objects entry
                                                       (what the MTC planning-scene server calls target_object_id)

No cloud and no API key: only a running `ollama serve` with the model pulled.
"""
import base64
import json
import re
import threading
import time
import urllib.error
import urllib.request
from typing import List, Optional, Tuple

import cv2
import message_filters
import numpy as np
import rclpy
import tf2_geometry_msgs  # noqa: F401  (registers PoseStamped transforms)
import tf2_ros
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import String

from ur_perception.depth_pose_estimator import DepthPoseEstimator
from ur_perception.image_convert import NumpyBridge as CvBridge

_PATCH = 28   # Qwen2.5-VL sees the image in 28 px tiles; send a multiple so box coordinates map 1:1


def parse_bbox(text: str) -> Optional[Tuple[float, float, float, float]]:
    """First [x1, y1, x2, y2] found in the VLM reply (plain JSON, fenced JSON or free text)."""
    for m in re.finditer(r"\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,"
                         r"\s*(-?\d+(?:\.\d+)?)\s*\]", text):
        x1, y1, x2, y2 = (float(g) for g in m.groups())
        if x2 > x1 and y2 > y1:
            return x1, y1, x2, y2
    return None


def fit_size(w: int, h: int, max_side: int) -> Tuple[int, int]:
    """Size with the long side near max_side (enlarging small camera frames: a 20 px object is lost to a 3B VLM),
    both sides a multiple of _PATCH, keeping the aspect ratio."""
    s = max_side / max(w, h)
    return max(_PATCH, round(w * s / _PATCH) * _PATCH), max(_PATCH, round(h * s / _PATCH) * _PATCH)


class VlmGroundingNode(Node):
    def __init__(self) -> None:
        super().__init__('vlm_grounding_node')
        self.declare_parameter('model', 'qwen2.5vl:3b')
        self.declare_parameter('ollama_url', 'http://localhost:11434')
        self.declare_parameter('timeout_s', 60.0)
        self.declare_parameter('max_side_px', 896)
        self.declare_parameter('color_topic', '/camera_head/color/image_raw')
        self.declare_parameter('depth_topic', '/camera_head/depth/image_rect_raw')
        self.declare_parameter('camera_info_topic', '/camera_head/camera_info')
        self.declare_parameter('depth_scale', 1.0)
        self.declare_parameter('min_depth_m', 0.1)
        self.declare_parameter('max_depth_m', 2.0)
        self.declare_parameter('match_radius_m', 0.05)
        self._model = self.get_parameter('model').value
        self._url = self.get_parameter('ollama_url').value.rstrip('/')
        self._timeout = float(self.get_parameter('timeout_s').value)
        self._max_side = int(self.get_parameter('max_side_px').value)
        self._depth_scale = float(self.get_parameter('depth_scale').value)
        self._min_d = float(self.get_parameter('min_depth_m').value)
        self._max_d = float(self.get_parameter('max_depth_m').value)
        self._match_r = float(self.get_parameter('match_radius_m').value)

        self._bridge = CvBridge()
        self._lock = threading.Lock()
        self._frame = None          # (bgr, depth, stamp, frame_id)
        self._estimator: Optional[DepthPoseEstimator] = None
        self._detected: List = []
        self._detected_t = 0.0
        self._busy = False

        self._tf_buffer = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        info_qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT,
                              durability=DurabilityPolicy.VOLATILE)
        self.create_subscription(CameraInfo, self.get_parameter('camera_info_topic').value,
                                 self._info_cb, info_qos)
        color = message_filters.Subscriber(self, Image, self.get_parameter('color_topic').value)
        depth = message_filters.Subscriber(self, Image, self.get_parameter('depth_topic').value)
        self._sync = message_filters.ApproximateTimeSynchronizer([color, depth], 5, 0.1)
        self._sync.registerCallback(self._frame_cb)
        try:
            from ur_interfaces.msg import DetectedObjectArray
            self.create_subscription(DetectedObjectArray, '/detected_objects', self._detected_cb, 10)
        except ImportError:
            self.get_logger().warn('ur_interfaces not available: target_object_id will not be published')

        self._pose_pub = self.create_publisher(PoseStamped, '/vlm/target_pose', 10)
        self._id_pub = self.create_publisher(String, '/vlm/target_object_id', 10)
        self.create_subscription(String, '/vlm/query', self._query_cb, 10)
        self.get_logger().info(f"VLM grounding ready: model={self._model} at {self._url}; "
                               "publish a text query on /vlm/query")

    # ------------------------------------------------------------------ inputs
    @staticmethod
    def _optical_frame(frame_id: str) -> str:
        """gz publishes images in <name>_depth_frame (x forward); the pixel maths needs the optical child
        frame (x right, y down, z forward), which the URDF already has (same conversion as object_detector_node)."""
        suffix = '_depth_frame'
        return frame_id[:-len(suffix)] + '_depth_optical_frame' if frame_id.endswith(suffix) else frame_id

    def _detected_cb(self, msg) -> None:
        # the detector also publishes empty arrays on frames where the colour mask misses: keep the last non-empty one
        if msg.objects:
            self._detected = list(msg.objects)
            self._detected_t = time.time()

    def _info_cb(self, msg: CameraInfo) -> None:
        if self._estimator is None:
            k = msg.k
            self._estimator = DepthPoseEstimator(fx=k[0], fy=k[4], cx=k[2], cy=k[5],
                                                 depth_scale=self._depth_scale, patch_radius=5)

    def _frame_cb(self, color_msg: Image, depth_msg: Image) -> None:
        try:
            bgr = self._bridge.imgmsg_to_cv2(color_msg, desired_encoding='bgr8')
            depth = self._bridge.imgmsg_to_cv2(depth_msg, desired_encoding='passthrough')
        except Exception as e:  # noqa: BLE001
            self.get_logger().warn(f"image conversion failed: {e}", throttle_duration_sec=5.0)
            return
        with self._lock:
            self._frame = (bgr, depth, color_msg.header.stamp,
                           self._optical_frame(depth_msg.header.frame_id or color_msg.header.frame_id))

    def _query_cb(self, msg: String) -> None:
        if self._busy:
            self.get_logger().warn('VLM query already running, ignoring this one')
            return
        self._busy = True
        threading.Thread(target=self._ground, args=(msg.data.strip(),), daemon=True).start()

    # ------------------------------------------------------------------ VLM
    def _ask_vlm(self, bgr: np.ndarray, query: str):
        """Returns (bbox in original pixel coordinates or None, raw reply)."""
        h, w = bgr.shape[:2]
        sw, sh = fit_size(w, h, self._max_side)
        ok, png = cv2.imencode('.png', cv2.resize(bgr, (sw, sh), interpolation=cv2.INTER_CUBIC if sw > w else cv2.INTER_AREA))
        if not ok:
            return None, ''
        prompt = (f'Locate "{query}" in the image. Reply with JSON only: '
                  '{"bbox_2d": [x1, y1, x2, y2]} in pixel coordinates of this image. '
                  'If it is not visible reply {"bbox_2d": null}.')
        body = json.dumps({'model': self._model, 'stream': False, 'options': {'temperature': 0},
                           'messages': [{'role': 'user', 'content': prompt,
                                         'images': [base64.b64encode(png.tobytes()).decode()]}]}).encode()
        req = urllib.request.Request(f'{self._url}/api/chat', body, {'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=self._timeout) as r:
            reply = json.loads(r.read())['message']['content']
        box = parse_bbox(reply)
        if box is None:
            return None, reply
        sx, sy = w / sw, h / sh
        return (box[0] * sx, box[1] * sy, box[2] * sx, box[3] * sy), reply

    # ------------------------------------------------------------------ grounding
    def _ground(self, query: str) -> None:
        try:
            with self._lock:
                frame = self._frame
            if frame is None or self._estimator is None:
                self.get_logger().warn('no image / camera info yet')
                return
            bgr, depth, stamp, frame_id = frame
            try:
                bbox, reply = self._ask_vlm(bgr, query)
            except (urllib.error.URLError, TimeoutError, KeyError, ValueError) as e:
                self.get_logger().error(f"Ollama request failed ({e}); is `ollama serve` running with "
                                        f"{self._model} pulled?")
                return
            if bbox is None:
                self.get_logger().warn(f'VLM found no "{query}": {reply[:120]!r}')
                return
            h, w = bgr.shape[:2]
            x1, y1, x2, y2 = (int(round(v)) for v in bbox)
            x1, x2 = max(0, x1), min(w - 1, x2)
            y1, y2 = max(0, y1), min(h - 1, y2)
            # The 3B model's box is loose, so the depth at its centre often lands on the background. Take the
            # pose from the detected object inside the box; with none inside, report nothing rather than guess.
            obj = self._object_in_box(bbox, frame_id)
            if obj is None:
                self.get_logger().warn(f'VLM box ({x1},{y1},{x2},{y2}) for "{query}" contains no detected object; '
                                       'no target published')
                return
            pose = PoseStamped()
            pose.header.frame_id = 'base_link'
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.pose.position.x, pose.pose.position.y, pose.pose.position.z = (
                obj.position.x, obj.position.y, obj.position.z)
            pose.pose.orientation.w = 1.0
            self._pose_pub.publish(pose)
            self._id_pub.publish(String(data=obj.id))
            self.get_logger().info(f'"{query}": box=({x1},{y1},{x2},{y2}) -> {obj.id} at base_link '
                                   f'({obj.position.x:.3f}, {obj.position.y:.3f}, {obj.position.z:.3f})')
        finally:
            self._busy = False

    def _object_in_box(self, bbox, cam_frame: str):
        """Detected object whose centre projects inside the VLM box (closest to the box centre), or None."""
        est = self._estimator
        if est is None or not self._detected or time.time() - self._detected_t > 10.0:
            self.get_logger().warn(f'no recent detected objects (estimator={est is not None}, '
                                   f'n={len(self._detected)}, age={time.time() - self._detected_t:.1f}s)')
            return None
        try:
            tf = self._tf_buffer.lookup_transform(cam_frame, 'base_link', rclpy.time.Time(),
                                                  timeout=rclpy.duration.Duration(seconds=0.5))
        except Exception as e:  # noqa: BLE001
            self.get_logger().warn(f'TF {cam_frame} <- base_link failed: {e}')
            return None
        x1, y1, x2, y2 = bbox
        bcx, bcy = 0.5 * (x1 + x2), 0.5 * (y1 + y2)
        k = est.intrinsics
        best, best_d = None, float('inf')
        for o in self._detected:
            ps = PoseStamped()
            ps.header.frame_id = 'base_link'
            ps.pose.position.x, ps.pose.position.y, ps.pose.position.z = (
                o.position.x, o.position.y, o.position.z)
            ps.pose.orientation.w = 1.0
            c = tf2_geometry_msgs.do_transform_pose_stamped(ps, tf).pose.position
            if c.z <= 0.05:
                continue
            u, v = k['fx'] * c.x / c.z + k['cx'], k['fy'] * c.y / c.z + k['cy']
            self.get_logger().info(f'  {o.id}: cam=({c.x:.3f}, {c.y:.3f}, {c.z:.3f}) -> pixel ({u:.0f}, {v:.0f}) '
                                   f'vs box ({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}) in {cam_frame}')
            if x1 <= u <= x2 and y1 <= v <= y2:
                d = float(np.hypot(u - bcx, v - bcy))
                if d < best_d:
                    best, best_d = o, d
        return best

    def _nearest_id(self, x: float, y: float) -> str:
        best, best_d = '', self._match_r
        for o in self._detected:
            d = float(np.hypot(o.position.x - x, o.position.y - y))
            if d < best_d:
                best, best_d = o.id, d
        return best


def main(args=None) -> None:
    rclpy.init(args=args)
    node = VlmGroundingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
