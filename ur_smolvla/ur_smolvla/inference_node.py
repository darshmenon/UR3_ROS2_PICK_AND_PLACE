#!/usr/bin/env python3
"""
OpenVLA inference node for UR3 pick-and-place.

Replaces SmolVLA (requires Python 3.11) with OpenVLA which runs on
Python 3.10 using the already-installed torch + transformers stack.

Model: openvla/openvla-7b  (downloads ~15 GB on first run, cached after)
  - Input:  RGB image (256x256) + natural language task string
  - Output: 7D action (6 arm joint deltas + 1 gripper)

Usage:
    ros2 launch ur_smolvla smolvla_inference.launch.py \
      task:="pick the red block and place it in the bin"
"""

import threading

import numpy as np
import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image, JointState
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

try:
    from cv_bridge import CvBridge
    CV_BRIDGE_AVAILABLE = True
except ImportError:
    CV_BRIDGE_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import AutoModelForVision2Seq, AutoProcessor
    from PIL import Image as PILImage
    OPENVLA_AVAILABLE = True
except ImportError:
    OPENVLA_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


ARM_JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
GRIPPER_JOINT_NAME = "finger_joint"
IMAGE_SIZE = 256   # OpenVLA expects 256x256


class OpenVLAInferenceNode(Node):
    """
    Runs OpenVLA policy inference and sends JointTrajectory commands.

    Parameters
    ----------
    checkpoint   : HuggingFace model ID or local path  (default: openvla/openvla-7b)
    task         : Natural language task description
    camera_topic : RGB image topic  (default: /camera_head/color/image_raw)
    control_hz   : Inference rate in Hz  (default: 10)
    action_scale : Scale applied to predicted joint deltas  (default: 0.05)
    """

    def __init__(self):
        super().__init__("openvla_inference_node")

        self.declare_parameter("checkpoint",   "openvla/openvla-7b")
        self.declare_parameter("task",         "pick the red block and place it in the bin")
        self.declare_parameter("camera_topic", "/camera_head/color/image_raw")
        self.declare_parameter("control_hz",   10.0)
        self.declare_parameter("action_scale", 0.05)
        self.declare_parameter("use_sim_time", True)

        checkpoint  = self.get_parameter("checkpoint").value
        self._task  = self.get_parameter("task").value
        cam_topic   = self.get_parameter("camera_topic").value
        hz          = float(self.get_parameter("control_hz").value)
        self._scale = float(self.get_parameter("action_scale").value)

        if not CV_BRIDGE_AVAILABLE:
            self.get_logger().error("cv_bridge not available")
            return
        if not TORCH_AVAILABLE:
            self.get_logger().error("torch not available")
            return
        if not OPENVLA_AVAILABLE:
            self.get_logger().error(
                "transformers or Pillow not available — run: pip3 install transformers pillow"
            )
            return

        self._bridge = CvBridge()
        self._lock   = threading.Lock()
        self._latest_image = None
        self._qpos = np.zeros(6, dtype=np.float32)
        self._have_joints = False

        self.get_logger().info(f"Loading OpenVLA from '{checkpoint}' ...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._processor = AutoProcessor.from_pretrained(
            checkpoint, trust_remote_code=True
        )
        self._model = AutoModelForVision2Seq.from_pretrained(
            checkpoint,
            attn_implementation="flash_attention_2" if torch.cuda.is_available() else "eager",
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        ).to(device)
        self._device = device
        self.get_logger().info(f"OpenVLA ready on {device}  |  task: '{self._task}'")

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.create_subscription(Image,      cam_topic,       self._image_cb, sensor_qos)
        self.create_subscription(JointState, "/joint_states", self._joint_cb, sensor_qos)

        self._arm_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10
        )
        self._gripper_pub = self.create_publisher(
            JointTrajectory, "/gripper_controller/joint_trajectory", 10
        )
        self.create_timer(1.0 / hz, self._step)

    # ── callbacks ────────────────────────────────────────────────────────
    def _image_cb(self, msg: Image):
        try:
            cv_img = self._bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
            with self._lock:
                self._latest_image = cv_img
        except Exception as e:
            self.get_logger().warn(f"Image conversion failed: {e}")

    def _joint_cb(self, msg: JointState):
        name_idx = {n: i for i, n in enumerate(msg.name)}
        for ji, jname in enumerate(ARM_JOINT_NAMES):
            if jname in name_idx:
                self._qpos[ji] = msg.position[name_idx[jname]]
        self._have_joints = True

    # ── inference ────────────────────────────────────────────────────────
    def _step(self):
        if not self._have_joints:
            return
        with self._lock:
            img = self._latest_image
        if img is None:
            return

        try:
            if CV2_AVAILABLE:
                img = cv2.resize(img, (IMAGE_SIZE, IMAGE_SIZE))
            pil_img = PILImage.fromarray(img)

            prompt = f"In: What action should the robot take to {self._task}?\nOut:"
            inputs = self._processor(prompt, pil_img).to(
                self._device, dtype=torch.bfloat16
            )

            with torch.no_grad():
                action = self._model.predict_action(
                    **inputs, unnorm_key="bridge_orig", do_sample=False
                )

            action = np.array(action, dtype=np.float32).flatten()
            if len(action) < 7:
                return

            arm_target  = self._qpos + np.clip(action[:6], -1.0, 1.0) * self._scale
            gripper_pos = float(np.clip((action[6] + 1.0) / 2.0 * 0.8, 0.0, 0.8))

            self._publish_arm(arm_target)
            self._publish_gripper(gripper_pos)

        except Exception as e:
            self.get_logger().warn(f"Inference error: {e}", throttle_duration_sec=5.0)

    # ── publishers ───────────────────────────────────────────────────────
    def _publish_arm(self, positions):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names  = ARM_JOINT_NAMES
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.time_from_start = Duration(sec=0, nanosec=100_000_000)
        msg.points = [pt]
        self._arm_pub.publish(msg)

    def _publish_gripper(self, position: float):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names  = [GRIPPER_JOINT_NAME]
        pt = JointTrajectoryPoint()
        pt.positions = [position]
        pt.time_from_start = Duration(sec=0, nanosec=100_000_000)
        msg.points = [pt]
        self._gripper_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = OpenVLAInferenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
