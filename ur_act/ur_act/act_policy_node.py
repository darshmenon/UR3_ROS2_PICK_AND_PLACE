#!/usr/bin/env python3
"""
ACT policy inference node.

Subscribes to camera and joint states, runs the trained ACT model,
and publishes joint trajectories via the arm_controller.

Uses temporal ensemble to blend overlapping chunk predictions.
"""

import sys
import threading
from pathlib import Path

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import JointState, Image
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

try:
    from cv_bridge import CvBridge
except ImportError:
    raise ImportError("cv_bridge not found. Install ros-humble-cv-bridge.")

try:
    import torch
    import cv2
except ImportError as e:
    raise ImportError(f"Missing dependency: {e}")

# Allow running without colcon install
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ur_act.model import ACT, TemporalEnsemble

ARM_JOINTS = [
    "shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
    "wrist_1_joint", "wrist_2_joint", "wrist_3_joint",
]
GRIPPER_JOINT = "finger_joint"


class ACTPolicyNode(Node):
    def __init__(self):
        super().__init__("act_policy_node")

        # Parameters
        self.declare_parameter("model_path",  "")
        self.declare_parameter("chunk_size",  10)
        self.declare_parameter("d_model",     256)
        self.declare_parameter("nhead",       8)
        self.declare_parameter("enc_layers",  4)
        self.declare_parameter("dec_layers",  4)
        self.declare_parameter("latent_dim",  32)
        self.declare_parameter("image_height", 240)
        self.declare_parameter("image_width",  424)
        self.declare_parameter("control_rate_hz", 5.0)
        self.declare_parameter("temporal_gamma",  0.01)
        self.declare_parameter("step_dt_sec",     0.2)

        model_path = self.get_parameter("model_path").value
        chunk_size = self.get_parameter("chunk_size").value
        d_model    = self.get_parameter("d_model").value
        nhead      = self.get_parameter("nhead").value
        enc_layers = self.get_parameter("enc_layers").value
        dec_layers = self.get_parameter("dec_layers").value
        latent_dim = self.get_parameter("latent_dim").value
        self.img_h = self.get_parameter("image_height").value
        self.img_w = self.get_parameter("image_width").value
        rate_hz    = self.get_parameter("control_rate_hz").value
        gamma      = self.get_parameter("temporal_gamma").value
        self.step_dt = self.get_parameter("step_dt_sec").value

        if not model_path:
            self.get_logger().fatal("model_path parameter is required.")
            raise RuntimeError("model_path not set")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.get_logger().info(f"Loading model from {model_path} on {self.device}")

        # Load checkpoint — infer arch from saved args if present
        ckpt = torch.load(model_path, map_location=self.device)
        saved = ckpt.get("args", {})
        self.model = ACT(
            action_dim=7,
            chunk_size=saved.get("chunk_size", chunk_size),
            d_model=saved.get("d_model", d_model),
            nhead=saved.get("nhead", nhead),
            num_encoder_layers=saved.get("enc_layers", enc_layers),
            num_decoder_layers=saved.get("dec_layers", dec_layers),
            latent_dim=saved.get("latent_dim", latent_dim),
        ).to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()
        self.get_logger().info("Model loaded.")

        self.ensemble = TemporalEnsemble(
            chunk_size=saved.get("chunk_size", chunk_size),
            action_dim=7,
            gamma=gamma,
        )

        self._bridge = CvBridge()
        self._lock = threading.Lock()
        self._joints: np.ndarray | None = None   # (7,)
        self._rgb:    np.ndarray | None = None   # (H, W, 3) uint8

        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST, depth=1,
        )
        self.create_subscription(JointState, "/joint_states",
                                 self._joint_cb, 10)
        self.create_subscription(Image, "/camera_head/color/image_raw",
                                 self._rgb_cb, sensor_qos)

        self._traj_pub = self.create_publisher(
            JointTrajectory, "/arm_controller/joint_trajectory", 10)

        self.create_timer(1.0 / rate_hz, self._inference_cb)
        self.get_logger().info(
            f"ACT policy node ready at {rate_hz} Hz "
            f"(chunk_size={saved.get('chunk_size', chunk_size)}, "
            f"temporal_gamma={gamma})"
        )

    # ── callbacks ──────────────────────────────────────────────────────────

    def _joint_cb(self, msg: JointState):
        name_pos = dict(zip(msg.name, msg.position))
        arm = np.array([name_pos.get(j, 0.0) for j in ARM_JOINTS], dtype=np.float32)
        grip = np.array([name_pos.get(GRIPPER_JOINT, 0.0)], dtype=np.float32)
        with self._lock:
            self._joints = np.concatenate([arm, grip])

    def _rgb_cb(self, msg: Image):
        try:
            img = self._bridge.imgmsg_to_cv2(msg, desired_encoding="rgb8")
            if img.shape[:2] != (self.img_h, self.img_w):
                img = cv2.resize(img, (self.img_w, self.img_h),
                                 interpolation=cv2.INTER_LINEAR)
            with self._lock:
                self._rgb = img.copy()
        except Exception as e:
            self.get_logger().warn(f"RGB conversion failed: {e}", throttle_duration_sec=5.0)

    # ── inference ──────────────────────────────────────────────────────────

    def _inference_cb(self):
        with self._lock:
            joints = self._joints.copy() if self._joints is not None else None
            rgb    = self._rgb.copy()    if self._rgb    is not None else None

        if joints is None or rgb is None:
            return

        rgb_t = torch.from_numpy(
            np.transpose(rgb.astype(np.float32) / 255.0, (2, 0, 1))
        ).unsqueeze(0).to(self.device)
        j_t = torch.from_numpy(joints).unsqueeze(0).to(self.device)

        with torch.no_grad():
            pred, _, _ = self.model(rgb_t, j_t)   # (1, chunk_size, 7)

        chunk = pred.squeeze(0).cpu()              # (chunk_size, 7)
        self.ensemble.push(chunk)
        action = self.ensemble.get().numpy()       # (7,)

        arm_cmd  = action[:6].tolist()
        self._publish_trajectory(arm_cmd)

    def _publish_trajectory(self, positions: list):
        msg = JointTrajectory()
        msg.joint_names = ARM_JOINTS
        pt = JointTrajectoryPoint()
        pt.positions = positions
        pt.time_from_start = Duration(sec=0, nanosec=int(self.step_dt * 1e9))
        msg.points = [pt]
        self._traj_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ACTPolicyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
