import sys
from pathlib import Path

import numpy as np
import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import JointState

# The system triton package segfaults on import when torch builds an Adam
# optimizer (SAC._build). Block it before torch/stable_baselines3 load —
# CPU inference here never needs triton kernels anyway. Same fix as
# ur_rl_training/policy_node.py.
sys.modules["triton"] = None
from stable_baselines3 import SAC
from tf2_ros import Buffer, TransformException, TransformListener
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

ARM_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
GRIPPER_JOINT = "finger_joint"

def resolve_default_model_path():
    """Walk up from this file to find the workspace root, then pick the latest best_model.zip."""
    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        runs_dir = parent / "models" / "gazebo_single_arm"
        if runs_dir.is_dir():
            candidates = sorted(runs_dir.glob("*/best_model.zip"), reverse=True)
            if candidates:
                return str(candidates[0])
    return ""


DEFAULT_MODEL_PATH = resolve_default_model_path()
GRASP_CLOSE_THRESHOLD = 0.28
LIFT_Z = 0.10


class SharedArmPolicyNode(Node):
    def __init__(self):
        super().__init__("shared_arm_policy_node")

        self.declare_parameter("model_path", DEFAULT_MODEL_PATH)
        self.declare_parameter("joint_state_topic", "/joint_states")
        self.declare_parameter(
            "arm_trajectory_topic",
            "/scaled_joint_trajectory_controller/joint_trajectory",
        )
        self.declare_parameter("gripper_trajectory_topic", "/gripper_controller/joint_trajectory")
        self.declare_parameter("arm_joint_names", ARM_JOINTS)
        self.declare_parameter("gripper_joint_names", [GRIPPER_JOINT])
        self.declare_parameter("control_rate_hz", 10.0)
        self.declare_parameter("action_scale", 1.2)
        self.declare_parameter("gripper_scale", 0.05)
        self.declare_parameter("gripper_close_scale", 0.20)
        self.declare_parameter("step_dt", 0.1)
        self.declare_parameter("publish_gripper", True)
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("ee_frame", "robotiq_arg2f_base_link")

        self.declare_parameter("ee_x", 0.0)
        self.declare_parameter("ee_y", 0.0)
        self.declare_parameter("ee_z", 0.0)
        self.declare_parameter("object_x", 0.35)
        self.declare_parameter("object_y", 0.0)
        self.declare_parameter("object_z", 0.045)
        self.declare_parameter("drop_x", 0.35)
        self.declare_parameter("drop_y", 0.20)
        self.declare_parameter("drop_z", 0.025)
        self.declare_parameter("phase", 0.0)

        model_path = str(self.get_parameter("model_path").value) or DEFAULT_MODEL_PATH
        if not model_path:
            raise RuntimeError(
                "No model found in models/gazebo_single_arm/. "
                "Pass -p model_path:=/path/to/best_model.zip"
            )
        self._arm_joint_names = [str(name) for name in self.get_parameter("arm_joint_names").value]
        self._gripper_joint_names = [str(name) for name in self.get_parameter("gripper_joint_names").value]
        self._action_scale = float(self.get_parameter("action_scale").value)
        self._gripper_scale = float(self.get_parameter("gripper_scale").value)
        self._gripper_close_scale = float(self.get_parameter("gripper_close_scale").value)
        self._step_dt = float(self.get_parameter("step_dt").value)
        self._publish_gripper = bool(self.get_parameter("publish_gripper").value)
        self._base_frame = str(self.get_parameter("base_frame").value)
        self._ee_frame = str(self.get_parameter("ee_frame").value)
        self._warned_missing_arm_joints = set()
        self._warned_missing_gripper_joints = set()
        self._warned_tf_lookup = False

        if len(self._arm_joint_names) != 6:
            raise ValueError("arm_joint_names must contain exactly 6 joints for the shared-arm policy.")

        self.qpos = np.zeros(len(self._arm_joint_names), dtype=np.float32)
        self.qvel = np.zeros(len(self._arm_joint_names), dtype=np.float32)
        self.gripper_qpos = np.float32(0.0)
        self._prev_pos = np.zeros(len(self._arm_joint_names), dtype=np.float32)
        self._prev_time = None
        self._have_joint_state = False
        self._phase = float(self.get_parameter("phase").value)
        self._latest_ee_pos = self._param_vec("ee")

        self.get_logger().info(f"Loading shared-arm SAC model from {model_path}")
        self.model = SAC.load(model_path)
        self.get_logger().info("Shared-arm model loaded.")

        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, self, spin_thread=True)

        joint_state_topic = str(self.get_parameter("joint_state_topic").value)
        arm_trajectory_topic = str(self.get_parameter("arm_trajectory_topic").value)
        gripper_trajectory_topic = str(self.get_parameter("gripper_trajectory_topic").value)
        control_rate_hz = float(self.get_parameter("control_rate_hz").value)

        self.create_subscription(JointState, joint_state_topic, self._joint_cb, 10)
        self._arm_pub = self.create_publisher(JointTrajectory, arm_trajectory_topic, 10)
        self._gripper_pub = self.create_publisher(JointTrajectory, gripper_trajectory_topic, 10)
        self.create_timer(1.0 / control_rate_hz, self._step)

    def _joint_cb(self, msg):
        name_to_idx = {name: idx for idx, name in enumerate(msg.name)}
        now = self.get_clock().now().nanoseconds * 1e-9

        for joint_idx, joint_name in enumerate(self._arm_joint_names):
            if joint_name not in name_to_idx:
                if joint_name not in self._warned_missing_arm_joints:
                    self.get_logger().warning(f"Joint state is missing arm joint '{joint_name}'")
                    self._warned_missing_arm_joints.add(joint_name)
                continue
            msg_idx = name_to_idx[joint_name]
            pos = np.float32(msg.position[msg_idx])
            self.qpos[joint_idx] = pos
            if self._prev_time is not None and (now - self._prev_time) > 0:
                self.qvel[joint_idx] = (pos - self._prev_pos[joint_idx]) / (now - self._prev_time)
            self._prev_pos[joint_idx] = pos

        for joint_name in self._gripper_joint_names:
            if joint_name in name_to_idx:
                self.gripper_qpos = np.float32(msg.position[name_to_idx[joint_name]])
                break
        else:
            for joint_name in self._gripper_joint_names:
                if joint_name not in self._warned_missing_gripper_joints:
                    self.get_logger().warning(f"Joint state is missing gripper joint '{joint_name}'")
                    self._warned_missing_gripper_joints.add(joint_name)

        self._prev_time = now
        self._have_joint_state = True

    def _param_vec(self, prefix):
        return np.array(
            [
                float(self.get_parameter(f"{prefix}_x").value),
                float(self.get_parameter(f"{prefix}_y").value),
                float(self.get_parameter(f"{prefix}_z").value),
            ],
            dtype=np.float32,
        )

    def _obs(self):
        ee_pos = self._lookup_ee_pos()
        self._phase = self._infer_phase(ee_pos)
        return np.concatenate(
            [
                self.qpos,
                self.qvel,
                ee_pos,
                self._param_vec("object"),
                self._param_vec("drop"),
                np.array([self.gripper_qpos], dtype=np.float32),
                np.array([self._phase], dtype=np.float32),
            ]
        ).astype(np.float32)

    def _lookup_ee_pos(self):
        try:
            transform = self._tf_buffer.lookup_transform(
                self._base_frame,
                self._ee_frame,
                Time(),
            )
            translation = transform.transform.translation
            self._latest_ee_pos = np.array(
                [translation.x, translation.y, translation.z],
                dtype=np.float32,
            )
            self._warned_tf_lookup = False
        except TransformException as exc:
            if not self._warned_tf_lookup:
                self.get_logger().warning(
                    f"Falling back to ee_* parameters because TF lookup "
                    f"{self._base_frame} -> {self._ee_frame} failed: {exc}"
                )
                self._warned_tf_lookup = True
        return self._latest_ee_pos

    def _infer_phase(self, ee_pos):
        obj = self._param_vec("object")
        drop = self._param_vec("drop")

        ee_to_obj = float(np.linalg.norm(ee_pos - obj))
        ee_to_obj_xy = float(np.linalg.norm(ee_pos[:2] - obj[:2]))
        ee_height_err = float(abs(ee_pos[2] - (obj[2] + 0.03)))
        drop_xy = float(np.linalg.norm(ee_pos[:2] - drop[:2]))
        gripper_closed = float(self.gripper_qpos) > GRASP_CLOSE_THRESHOLD
        near_grasp = ee_to_obj < 0.15 or (ee_to_obj_xy < 0.07 and ee_height_err < 0.035)
        lifted = float(ee_pos[2]) >= float(obj[2] + LIFT_Z)

        phase = self._phase
        if phase < 0.5:
            if near_grasp:
                phase = 1.0
            else:
                phase = 0.0
        elif phase < 1.5:
            if gripper_closed:
                phase = 2.0
            elif near_grasp:
                phase = 1.0
            else:
                phase = 0.0
        elif phase < 2.5:
            if not gripper_closed:
                phase = 1.0
            elif lifted:
                phase = 3.0
            else:
                phase = 2.0
        else:
            if not gripper_closed:
                phase = 1.0
            elif lifted or drop_xy < 0.12:
                phase = 3.0
            else:
                phase = 2.0
        return np.float32(phase)

    def _step(self):
        if not self._have_joint_state:
            return

        action, _ = self.model.predict(self._obs(), deterministic=True)
        action = np.asarray(action, dtype=np.float32)
        arm_delta = np.clip(action[:6], -1.0, 1.0) * self._action_scale * self._step_dt
        arm_target = self.qpos + arm_delta

        self._publish_arm(arm_target)
        if self._publish_gripper and action.shape[0] >= 7:
            gripper_action = float(np.clip(action[6], -1.0, 1.0))
            gripper_scale = self._gripper_close_scale if gripper_action > 0.0 else self._gripper_scale
            gripper_target = float(self.gripper_qpos + gripper_action * gripper_scale)
            self._publish_gripper_target(gripper_target)

    def _duration(self):
        nanoseconds = max(int(self._step_dt * 1e9), 1)
        return Duration(
            sec=nanoseconds // 1_000_000_000,
            nanosec=nanoseconds % 1_000_000_000,
        )

    def _publish_arm(self, positions):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = self._arm_joint_names
        point = JointTrajectoryPoint()
        point.positions = [float(value) for value in positions]
        point.time_from_start = self._duration()
        msg.points = [point]
        self._arm_pub.publish(msg)

    def _publish_gripper_target(self, position):
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = self._gripper_joint_names
        point = JointTrajectoryPoint()
        point.positions = [position for _ in self._gripper_joint_names]
        point.time_from_start = self._duration()
        msg.points = [point]
        self._gripper_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SharedArmPolicyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
