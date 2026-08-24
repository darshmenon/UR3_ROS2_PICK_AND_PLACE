#!/usr/bin/env python3
"""
Flow-matching inference node for UR3 pick-and-place.

Runs the DINOv2 + flow-matching action-chunk policy (ur_flow_policy.model),
trained by scripts/train_flow_policy.py on ur_data_collector HDF5 demos.

Each control tick:
  1. Encode the current image once with the (frozen) DINOv2 backbone.
  2. Sample a new action chunk by integrating the flow-matching ODE from
     noise (t=0) to data (t=1) with a fixed-step Euler solver, reusing the
     cached image features across every ODE step.
  3. Temporal ensembling: blend the freshly sampled chunk with overlapping
     predictions from the last few chunks (weighted by how close each
     prediction is to the step it covers) so the executed trajectory doesn't
     jump between independently-sampled chunks — this is the "temporal
     consistency" behavior the chunk_size-length carry-over buffer provides.

Usage:
    ros2 launch ur_flow_policy flow_policy_inference.launch.py \
      checkpoint:=/path/to/best_policy.pt
"""

import threading
from collections import deque

import numpy as np
import rclpy
from builtin_interfaces.msg import Duration
from control_msgs.action import GripperCommand
from rclpy.action import ActionClient
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
    from transformers import AutoImageProcessor
    from PIL import Image as PILImage
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from ur_flow_policy.model import FlowMatchingPolicy


ARM_JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
GRIPPER_JOINT_NAME = "finger_joint"
ACTION_DIM = 7


class FlowPolicyInferenceNode(Node):
    """
    Runs the flow-matching policy and sends JointTrajectory commands.

    Parameters
    ----------
    checkpoint            : Path to a .pt checkpoint saved by train_flow_policy.py
    camera_topic          : RGB image topic  (default: /camera_head/color/image_raw)
    control_hz            : Control-loop rate in Hz  (default: 10)
    action_scale          : Scale applied to predicted joint deltas from the
                             chunk's first step  (default: 1.0 — the policy
                             predicts absolute target positions, see train_bc.py)
    chunk_size            : Action-chunk length  (default: 16, must match training)
    ode_steps             : Euler steps used to integrate the flow ODE  (default: 10)
    temporal_ensemble_m   : Exponential decay rate for blending overlapping
                             chunk predictions  (default: 0.1; 0 disables ensembling)
    dinov2_backbone       : Must match the checkpoint's backbone
    """

    def __init__(self):
        super().__init__("flow_policy_inference_node")

        self.declare_parameter("checkpoint", "")
        self.declare_parameter("camera_topic", "/camera_head/color/image_raw")
        self.declare_parameter("control_hz", 10.0)
        self.declare_parameter("action_scale", 1.0)
        self.declare_parameter("chunk_size", 16)
        self.declare_parameter("ode_steps", 10)
        self.declare_parameter("temporal_ensemble_m", 0.1)
        self.declare_parameter("dinov2_backbone", "facebook/dinov2-base")
        self.declare_parameter("use_sim_time", True)
        self.declare_parameter("enabled", True)

        checkpoint = self.get_parameter("checkpoint").value
        cam_topic = self.get_parameter("camera_topic").value
        hz = float(self.get_parameter("control_hz").value)
        self._scale = float(self.get_parameter("action_scale").value)
        self._chunk_size = int(self.get_parameter("chunk_size").value)
        self._ode_steps = int(self.get_parameter("ode_steps").value)
        self._ensemble_m = float(self.get_parameter("temporal_ensemble_m").value)
        backbone = self.get_parameter("dinov2_backbone").value
        self._enabled = bool(self.get_parameter("enabled").value)

        if not CV_BRIDGE_AVAILABLE:
            self.get_logger().error("cv_bridge not available")
            return
        if not TORCH_AVAILABLE:
            self.get_logger().error("torch not available")
            return
        if not TRANSFORMERS_AVAILABLE:
            self.get_logger().error(
                "transformers or Pillow not available — run: pip3 install transformers pillow"
            )
            return
        if not checkpoint:
            self.get_logger().error("'checkpoint' parameter is required")
            return

        self._bridge = CvBridge()
        self._lock = threading.Lock()
        self._latest_image = None
        self._qpos = np.zeros(6, dtype=np.float32)
        self._gripper_pos = 0.0
        self._have_joints = False

        self.get_logger().info(f"Loading flow-matching policy from '{checkpoint}' ...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self._device = device

        state = torch.load(checkpoint, map_location=device)
        ckpt_args = state.get("args", {})
        self._model = FlowMatchingPolicy(
            chunk_size=ckpt_args.get("chunk_size", self._chunk_size),
            action_dim=ACTION_DIM,
            proprio_dim=ACTION_DIM,
            hidden_dim=ckpt_args.get("hidden_dim", 256),
            depth=ckpt_args.get("depth", 6),
            dinov2_backbone=ckpt_args.get("dinov2_backbone", backbone),
        ).to(device)
        self._model.load_state_dict(state["model_state_dict"])
        self._model.eval()
        self._chunk_size = self._model.chunk_size

        self._processor = AutoImageProcessor.from_pretrained(
            ckpt_args.get("dinov2_backbone", backbone)
        )

        # Temporal ensembling buffer: deque of (start_step, chunk_tensor[chunk_size, ACTION_DIM])
        self._chunk_buffer = deque()
        self._abs_step = 0

        self.get_logger().info(
            f"Flow-matching policy ready on {device} "
            f"(chunk_size={self._chunk_size}, ode_steps={self._ode_steps})"
        )

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )
        self.create_subscription(Image, cam_topic, self._image_cb, sensor_qos)
        self.create_subscription(JointState, "/joint_states", self._joint_cb, sensor_qos)

        self._arm_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10
        )
        self._grp_client = ActionClient(self, GripperCommand, "/gripper_controller/gripper_cmd")
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
        if GRIPPER_JOINT_NAME in name_idx:
            self._gripper_pos = msg.position[name_idx[GRIPPER_JOINT_NAME]]
        self._have_joints = True

    # ── flow-matching sampling ──────────────────────────────────────────
    def _sample_chunk(self, pixel_values, proprio) -> "torch.Tensor":
        """Euler-integrates the flow ODE from noise (t=0) to data (t=1),
        reusing one cached DINOv2 encode across every ODE step."""
        with torch.no_grad():
            image_features = self._model.encode_image(pixel_values)
            x = torch.randn(1, self._chunk_size, ACTION_DIM, device=self._device)
            dt = 1.0 / self._ode_steps
            for step in range(self._ode_steps):
                t = torch.full((1,), step * dt, device=self._device)
                v = self._model(
                    proprio=proprio, noisy_actions=x, t=t, image_features=image_features
                )
                x = x + v * dt
        return x[0]  # (chunk_size, ACTION_DIM)

    def _ensembled_action(self, new_chunk) -> np.ndarray:
        """Blends every buffered chunk's prediction for the current absolute
        step, weighted by exp(-m * offset) — closer-to-execution predictions
        (small offset into their own chunk) count more."""
        self._chunk_buffer.append((self._abs_step, new_chunk))
        while self._chunk_buffer and self._chunk_buffer[0][0] + self._chunk_size <= self._abs_step:
            self._chunk_buffer.popleft()

        if self._ensemble_m <= 0.0:
            return new_chunk[0].cpu().numpy()

        weighted_sum = torch.zeros(ACTION_DIM, device=self._device)
        weight_total = 0.0
        for start_step, chunk in self._chunk_buffer:
            offset = self._abs_step - start_step
            if 0 <= offset < chunk.shape[0]:
                w = float(np.exp(-self._ensemble_m * offset))
                weighted_sum += w * chunk[offset]
                weight_total += w
        return (weighted_sum / weight_total).cpu().numpy()

    # ── control loop ─────────────────────────────────────────────────────
    def _step(self):
        if not self._enabled or not self._have_joints:
            return
        with self._lock:
            img = self._latest_image
        if img is None:
            return

        try:
            pil_img = PILImage.fromarray(img)
            pixel_values = self._processor(images=pil_img, return_tensors="pt")[
                "pixel_values"
            ].to(self._device)
            proprio = torch.from_numpy(
                np.concatenate([self._qpos, [self._gripper_pos]]).astype(np.float32)
            )[None, :].to(self._device)

            chunk = self._sample_chunk(pixel_values, proprio)
            action = self._ensembled_action(chunk)
            self._abs_step += 1

            if np.any(np.isnan(action)) or np.any(np.isinf(action)):
                self.get_logger().warn("Inference returned NaN/Inf — skipping step.")
                return

            arm_target = action[:6] * self._scale
            gripper_pos = float(np.clip(action[6], 0.0, 0.8))

            self._publish_arm(arm_target)
            self._publish_gripper(gripper_pos)

        except Exception as e:
            self.get_logger().warn(f"Inference error: {e}", throttle_duration_sec=5.0)

    # ── publishers ───────────────────────────────────────────────────────
    def _publish_arm(self, positions):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = ARM_JOINT_NAMES
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.time_from_start = Duration(sec=0, nanosec=100_000_000)
        msg.points = [pt]
        self._arm_pub.publish(msg)

    def _publish_gripper(self, position: float):
        if not self._grp_client.server_is_ready():
            return
        goal = GripperCommand.Goal()
        goal.command.position = float(np.clip(position, 0.0, 0.8))
        goal.command.max_effort = 50.0
        self._grp_client.send_goal_async(goal)


def main(args=None):
    rclpy.init(args=args)
    node = FlowPolicyInferenceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
