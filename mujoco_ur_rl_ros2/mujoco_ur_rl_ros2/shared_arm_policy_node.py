from pathlib import Path

import numpy as np
import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState
from stable_baselines3 import SAC
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

DEFAULT_MODEL_RELATIVE_PATH = (
    Path("models")
    / "shared_arm"
    / "shared_arm_8arm_all_samples_resume_20260410_1501"
    / "best_model.zip"
)


def resolve_default_model_path():
    module_path = Path(__file__).resolve()
    for parent in module_path.parents:
        candidate = parent / DEFAULT_MODEL_RELATIVE_PATH
        if candidate.exists():
            return str(candidate)
    return str(module_path.parents[1] / DEFAULT_MODEL_RELATIVE_PATH)


DEFAULT_MODEL_PATH = resolve_default_model_path()


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
        self.declare_parameter("action_scale", 0.2)
        self.declare_parameter("gripper_scale", 0.02)
        self.declare_parameter("step_dt", 0.1)
        self.declare_parameter("publish_gripper", True)

        self.declare_parameter("ee_x", 0.0)
        self.declare_parameter("ee_y", 0.0)
        self.declare_parameter("ee_z", 0.0)
        self.declare_parameter("object_x", -1.18)
        self.declare_parameter("object_y", 0.0)
        self.declare_parameter("object_z", 0.045)
        self.declare_parameter("drop_x", -1.25)
        self.declare_parameter("drop_y", 0.0)
        self.declare_parameter("drop_z", 0.02)
        self.declare_parameter("phase", 0.0)

        model_path = str(self.get_parameter("model_path").value) or DEFAULT_MODEL_PATH
        self._arm_joint_names = [str(name) for name in self.get_parameter("arm_joint_names").value]
        self._gripper_joint_names = [str(name) for name in self.get_parameter("gripper_joint_names").value]
        self._action_scale = float(self.get_parameter("action_scale").value)
        self._gripper_scale = float(self.get_parameter("gripper_scale").value)
        self._step_dt = float(self.get_parameter("step_dt").value)
        self._publish_gripper = bool(self.get_parameter("publish_gripper").value)
        self._warned_missing_arm_joints = set()
        self._warned_missing_gripper_joints = set()

        if len(self._arm_joint_names) != 6:
            raise ValueError("arm_joint_names must contain exactly 6 joints for the shared-arm policy.")

        self.qpos = np.zeros(len(self._arm_joint_names), dtype=np.float32)
        self.qvel = np.zeros(len(self._arm_joint_names), dtype=np.float32)
        self.gripper_qpos = np.float32(0.0)
        self._prev_pos = np.zeros(len(self._arm_joint_names), dtype=np.float32)
        self._prev_time = None
        self._have_joint_state = False

        self.get_logger().info(f"Loading shared-arm SAC model from {model_path}")
        self.model = SAC.load(model_path)
        self.get_logger().info("Shared-arm model loaded.")

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
        return np.concatenate(
            [
                self.qpos,
                self.qvel,
                self._param_vec("ee"),
                self._param_vec("object"),
                self._param_vec("drop"),
                np.array([self.gripper_qpos], dtype=np.float32),
                np.array([float(self.get_parameter("phase").value)], dtype=np.float32),
            ]
        ).astype(np.float32)

    def _step(self):
        if not self._have_joint_state:
            return

        action, _ = self.model.predict(self._obs(), deterministic=True)
        action = np.asarray(action, dtype=np.float32)
        arm_delta = np.clip(action[:6], -1.0, 1.0) * self._action_scale * self._step_dt
        arm_target = self.qpos + arm_delta

        self._publish_arm(arm_target)
        if self._publish_gripper and action.shape[0] >= 7:
            gripper_target = float(self.gripper_qpos + np.clip(action[6], -1.0, 1.0) * self._gripper_scale)
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
