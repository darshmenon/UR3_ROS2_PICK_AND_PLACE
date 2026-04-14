from pathlib import Path

import numpy as np
import rclpy
from builtin_interfaces.msg import Duration
from rclpy.node import Node
from sensor_msgs.msg import JointState
from stable_baselines3 import SAC
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

UR5E_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]

DEFAULT_MODEL_PATH = str(Path(__file__).resolve().parents[1] / "models" / "best_model.zip")


class URPolicyNode(Node):
    def __init__(self):
        super().__init__("ur_policy_node")

        self.declare_parameter("model_path", DEFAULT_MODEL_PATH)
        self.declare_parameter("target_x", 0.4)
        self.declare_parameter("target_y", 0.0)
        self.declare_parameter("target_z", 0.4)
        self.declare_parameter("joint_state_topic", "/joint_states")
        self.declare_parameter(
            "trajectory_topic",
            "/scaled_joint_trajectory_controller/joint_trajectory",
        )
        self.declare_parameter("control_rate_hz", 10.0)
        self.declare_parameter("action_scale", 0.5)
        self.declare_parameter("step_dt", 0.1)

        model_path = self.get_parameter("model_path").value
        target = np.array(
            [
                float(self.get_parameter("target_x").value),
                float(self.get_parameter("target_y").value),
                float(self.get_parameter("target_z").value),
            ],
            dtype=np.float32,
        )
        joint_state_topic = str(self.get_parameter("joint_state_topic").value)
        trajectory_topic = str(self.get_parameter("trajectory_topic").value)
        control_rate_hz = float(self.get_parameter("control_rate_hz").value)
        self._action_scale = float(self.get_parameter("action_scale").value)
        self._step_dt = float(self.get_parameter("step_dt").value)

        self.target = target
        self.qpos = np.zeros(6, dtype=np.float32)
        self.qvel = np.zeros(6, dtype=np.float32)
        self._prev_pos = np.zeros(6, dtype=np.float32)
        self._prev_time = None

        self.get_logger().info(f"Loading model from {model_path}")
        self.model = SAC.load(model_path)
        self.get_logger().info("Model loaded.")

        self.create_subscription(JointState, joint_state_topic, self._joint_cb, 10)
        self._trajectory_pub = self.create_publisher(JointTrajectory, trajectory_topic, 10)
        self.create_timer(1.0 / control_rate_hz, self._step)

    def _joint_cb(self, msg: JointState):
        name_to_idx = {name: idx for idx, name in enumerate(msg.name)}
        now = self.get_clock().now().nanoseconds * 1e-9

        for joint_idx, joint_name in enumerate(UR5E_JOINTS):
            if joint_name not in name_to_idx:
                continue

            msg_idx = name_to_idx[joint_name]
            self.qpos[joint_idx] = msg.position[msg_idx]
            if self._prev_time is not None and (now - self._prev_time) > 0:
                self.qvel[joint_idx] = (
                    msg.position[msg_idx] - self._prev_pos[joint_idx]
                ) / (now - self._prev_time)
            self._prev_pos[joint_idx] = msg.position[msg_idx]

        self._prev_time = now

    def _step(self):
        obs = np.concatenate([self.qpos, self.qvel, self.target]).astype(np.float32)
        action, _ = self.model.predict(obs, deterministic=True)

        target_pos = self.qpos + np.clip(action, -1.0, 1.0) * self._action_scale * self._step_dt

        msg = JointTrajectory()
        msg.joint_names = UR5E_JOINTS

        point = JointTrajectoryPoint()
        point.positions = target_pos.tolist()

        nanoseconds = max(int(self._step_dt * 1e9), 1)
        point.time_from_start = Duration(
            sec=nanoseconds // 1_000_000_000,
            nanosec=nanoseconds % 1_000_000_000,
        )
        msg.points = [point]
        self._trajectory_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = URPolicyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
