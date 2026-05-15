"""
ROS 2 deployment node — runs a trained SAC policy on the real UR3 in Gazebo.

Subscribes: /joint_states
Publishes:  /arm_controller/joint_trajectory   (JointTrajectory)
Actions:    /gripper_controller/gripper_cmd    (GripperCommand — matches GripperActionController)

Observation (23-dim, matches UR3PickPlaceEnv):
  qpos[6] + qvel[6] + ee_pos[3] + obj_pos[3] + drop_pos[3] + gripper[1] + phase[1]

EE position is read from TF (base_link → tool0) — no hardcoded FK.
Object position is passed as ROS parameters (update via rqt or your perception node).
"""

from pathlib import Path

import numpy as np
import rclpy
import tf2_ros
from control_msgs.action import GripperCommand
from rclpy.action import ActionClient
from rclpy.node import Node
from sensor_msgs.msg import JointState
from stable_baselines3 import SAC
from stable_baselines3.common.save_util import load_from_zip_file
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

_PKG = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = str(_PKG / "models" / "checkpoints" / "best_model.zip")


class PolicyNode(Node):
    def __init__(self):
        super().__init__("ur3_rl_policy_node")

        self.declare_parameter("model_path",              DEFAULT_MODEL_PATH)
        self.declare_parameter("joint_state_topic",       "/joint_states")
        self.declare_parameter("arm_trajectory_topic",    "/arm_controller/joint_trajectory")
        self.declare_parameter("gripper_trajectory_topic","/gripper_controller/joint_trajectory")
        self.declare_parameter("arm_joint_names",         ARM_JOINTS)
        self.declare_parameter("gripper_joint_names",     [GRIPPER_JOINT])
        self.declare_parameter("base_frame",              "base_link")
        self.declare_parameter("ee_frame",                "tool0")
        self.declare_parameter("control_rate_hz",         10.0)
        self.declare_parameter("action_scale",            0.1)
        self.declare_parameter("gripper_scale",           0.04)
        self.declare_parameter("step_dt",                 0.1)

        # Object / drop zone positions — update these to match your scene
        self.declare_parameter("object_x",  0.35)
        self.declare_parameter("object_y",  0.0)
        self.declare_parameter("object_z",  0.045)
        self.declare_parameter("drop_x",    0.35)
        self.declare_parameter("drop_y",    0.20)
        self.declare_parameter("drop_z",    0.02)
        self.declare_parameter("phase",     1.0)

        model_path = str(self.get_parameter("model_path").value)
        self._arm_joints     = [str(j) for j in self.get_parameter("arm_joint_names").value]
        self._gripper_joints = [str(j) for j in self.get_parameter("gripper_joint_names").value]
        self._action_scale   = float(self.get_parameter("action_scale").value)
        self._gripper_scale  = float(self.get_parameter("gripper_scale").value)
        self._step_dt        = float(self.get_parameter("step_dt").value)
        self._base_frame     = str(self.get_parameter("base_frame").value)
        self._ee_frame       = str(self.get_parameter("ee_frame").value)

        self.qpos         = np.zeros(6, dtype=np.float32)
        self.qvel         = np.zeros(6, dtype=np.float32)
        self.gripper_qpos = np.float32(0.0)
        self._ee_pos      = np.zeros(3, dtype=np.float32)
        self._prev_pos    = np.zeros(6, dtype=np.float32)
        self._prev_time   = None
        self._have_joints = False
        self._warned      = set()

        self.get_logger().info(f"Loading model: {model_path}")
        from gymnasium import spaces as _spaces
        from stable_baselines3.common.vec_env import DummyVecEnv
        import gymnasium as _gym

        class _DummyEnv(_gym.Env):
            observation_space = _spaces.Box(-np.inf, np.inf, shape=(23,), dtype=np.float32)
            action_space      = _spaces.Box(-1.0, 1.0,      shape=(7,),  dtype=np.float32)
            def reset(self, **kw): return self.observation_space.sample(), {}
            def step(self, _a):   return self.observation_space.sample(), 0.0, False, False, {}

        _, params, _ = load_from_zip_file(model_path, device="cpu")
        self.model = SAC("MlpPolicy", DummyVecEnv([_DummyEnv]),
                         policy_kwargs={"net_arch": [256, 256, 256]})
        self.model.set_parameters({"policy": params["policy"]}, exact_match=False)
        self.get_logger().info("Model loaded — starting control loop.")

        self._tf_buffer   = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)

        js_topic  = str(self.get_parameter("joint_state_topic").value)
        arm_topic = str(self.get_parameter("arm_trajectory_topic").value)
        grp_action = str(self.get_parameter("gripper_trajectory_topic").value).replace(
            "joint_trajectory", "gripper_cmd")
        hz = float(self.get_parameter("control_rate_hz").value)

        self.create_subscription(JointState, js_topic, self._joint_cb, 10)
        self._arm_pub    = self.create_publisher(JointTrajectory, arm_topic, 10)
        self._grp_client = ActionClient(self, GripperCommand, grp_action)
        self.create_timer(1.0 / hz, self._step)

    # ── joint state callback ─────────────────────────────────────────────────
    def _joint_cb(self, msg: JointState):
        name_map = {n: i for i, n in enumerate(msg.name)}
        now = self.get_clock().now().nanoseconds * 1e-9

        for ji, jname in enumerate(self._arm_joints):
            if jname not in name_map:
                if jname not in self._warned:
                    self.get_logger().warning(f"Missing joint: {jname}")
                    self._warned.add(jname)
                continue
            mi = name_map[jname]
            pos = np.float32(msg.position[mi])
            if self._prev_time and (now - self._prev_time) > 0:
                self.qvel[ji] = (pos - self._prev_pos[ji]) / (now - self._prev_time)
            self.qpos[ji] = pos
            self._prev_pos[ji] = pos

        for jname in self._gripper_joints:
            if jname in name_map:
                self.gripper_qpos = np.float32(msg.position[name_map[jname]])
                break

        self._prev_time   = now
        self._have_joints = True

    # ── EE from TF ───────────────────────────────────────────────────────────
    def _update_ee(self):
        try:
            t = self._tf_buffer.lookup_transform(
                self._base_frame, self._ee_frame, rclpy.time.Time()
            )
            self._ee_pos = np.array([
                t.transform.translation.x,
                t.transform.translation.y,
                t.transform.translation.z,
            ], dtype=np.float32)
        except Exception:
            pass

    def _param_vec(self, prefix):
        return np.array([
            float(self.get_parameter(f"{prefix}_x").value),
            float(self.get_parameter(f"{prefix}_y").value),
            float(self.get_parameter(f"{prefix}_z").value),
        ], dtype=np.float32)

    # ── control step ─────────────────────────────────────────────────────────
    def _step(self):
        if not self._have_joints:
            return
        self._update_ee()

        obs = np.concatenate([
            self.qpos,
            self.qvel,
            self._ee_pos,
            self._param_vec("object"),
            self._param_vec("drop"),
            np.array([self.gripper_qpos], dtype=np.float32),
            np.array([float(self.get_parameter("phase").value)], dtype=np.float32),
        ]).astype(np.float32)

        action, _ = self.model.predict(obs, deterministic=True)
        action = np.asarray(action, dtype=np.float32)

        arm_delta  = np.clip(action[:6], -1.0, 1.0) * self._action_scale
        arm_target = self.qpos + arm_delta
        self._publish_arm(arm_target)

        if action.shape[0] >= 7:
            grip_target = float(self.gripper_qpos + np.clip(action[6], -1.0, 1.0) * self._gripper_scale)
            self._publish_gripper(grip_target)

    # ── publishers ───────────────────────────────────────────────────────────
    def _publish_arm(self, positions):
        from builtin_interfaces.msg import Duration
        ns = max(int(self._step_dt * 1e9), 1)
        dur = Duration(sec=ns // 1_000_000_000, nanosec=ns % 1_000_000_000)
        msg = JointTrajectory()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names  = self._arm_joints
        pt = JointTrajectoryPoint()
        pt.positions = [float(v) for v in positions]
        pt.time_from_start = dur
        msg.points = [pt]
        self._arm_pub.publish(msg)

    def _publish_gripper(self, position):
        if not self._grp_client.server_is_ready():
            return
        goal = GripperCommand.Goal()
        goal.command.position   = float(np.clip(position, 0.0, 0.8))
        goal.command.max_effort = 50.0
        self._grp_client.send_goal_async(goal)


def main(args=None):
    rclpy.init(args=args)
    node = PolicyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
