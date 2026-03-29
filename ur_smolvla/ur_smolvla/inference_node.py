#!/usr/bin/env python3
"""
SmolVLA inference node for UR3 pick-and-place.

Subscribes to camera image + joint states, runs SmolVLA policy,
and publishes JointTrajectory commands to arm_controller.

Usage:
    # Install lerobot first:
    # python3.11 -m pip install "git+https://github.com/huggingface/lerobot.git#egg=lerobot[smolvla]"
    #
    # Run inference:
    # ros2 run ur_smolvla inference_node.py --ros-args -p checkpoint:=lerobot/smolvla_base -p task:="pick the red block"
"""

import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import JointState, Image
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

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
    from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
    SMOLVLA_AVAILABLE = True
except ImportError:
    SMOLVLA_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


ARM_JOINT_NAMES = [
    'shoulder_pan_joint',
    'shoulder_lift_joint',
    'elbow_joint',
    'wrist_1_joint',
    'wrist_2_joint',
    'wrist_3_joint',
]

GRIPPER_JOINT_NAME = 'finger_joint'

# SmolVLA expects 512x512 images
IMAGE_SIZE = 512

# Action chunk size — how many steps to execute before re-planning
ACTION_CHUNK = 8


class SmolVLAInferenceNode(Node):
    """
    Runs SmolVLA policy inference and sends JointTrajectory commands.

    Parameters
    ----------
    checkpoint : str
        HuggingFace repo ID or local path to SmolVLA checkpoint.
        Default: 'lerobot/smolvla_base'
    task : str
        Natural-language task description passed to the VLA.
        Default: 'pick the colored block and place it in the bin'
    inference_hz : float
        Rate at which to run inference (Hz). Default: 10.0
    step_duration_ms : int
        Duration per trajectory point in milliseconds. Default: 100
    """

    def __init__(self):
        super().__init__('smolvla_inference')

        self.declare_parameter('checkpoint', 'lerobot/smolvla_base')
        self.declare_parameter('task', 'pick the colored block and place it in the bin')
        self.declare_parameter('inference_hz', 10.0)
        self.declare_parameter('step_duration_ms', 100)

        self.checkpoint = self.get_parameter('checkpoint').value
        self.task = self.get_parameter('task').value
        inference_hz = self.get_parameter('inference_hz').value
        self.step_duration_ms = self.get_parameter('step_duration_ms').value

        self._check_deps()

        self.bridge = CvBridge() if CV_BRIDGE_AVAILABLE else None
        self.policy = None
        self.lock = threading.Lock()

        # Latest observations
        self.latest_image = None
        self.latest_joints = None  # dict: joint_name -> position

        # QoS for sensor topics
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        self.image_sub = self.create_subscription(
            Image,
            '/camera_head/color/image_raw',
            self._image_cb,
            sensor_qos,
        )

        self.joint_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self._joint_cb,
            10,
        )

        self.traj_pub = self.create_publisher(
            JointTrajectory,
            '/arm_controller/joint_trajectory',
            10,
        )

        # Load policy in background so node starts fast
        self._load_thread = threading.Thread(target=self._load_policy, daemon=True)
        self._load_thread.start()

        self.timer = self.create_timer(1.0 / inference_hz, self._inference_step)
        self.get_logger().info(
            f'SmolVLA inference node started. Checkpoint: {self.checkpoint}'
        )
        self.get_logger().info(f'Task: "{self.task}"')

    def _check_deps(self):
        missing = []
        if not NUMPY_AVAILABLE:
            missing.append('numpy')
        if not CV_BRIDGE_AVAILABLE:
            missing.append('cv_bridge')
        if not TORCH_AVAILABLE:
            missing.append('torch')
        if not SMOLVLA_AVAILABLE:
            missing.append(
                'lerobot[smolvla]  →  '
                'python3.11 -m pip install "git+https://github.com/huggingface/lerobot.git#egg=lerobot[smolvla]"'
            )
        if missing:
            self.get_logger().error('Missing dependencies:\n  ' + '\n  '.join(missing))
            if not SMOLVLA_AVAILABLE:
                raise RuntimeError('lerobot not installed. See message above.')

    def _load_policy(self):
        self.get_logger().info(f'Loading SmolVLA from {self.checkpoint} ...')
        try:
            policy = SmolVLAPolicy.from_pretrained(self.checkpoint)
            policy.eval()
            if TORCH_AVAILABLE and torch.cuda.is_available():
                policy = policy.cuda()
                self.get_logger().info('Policy loaded on GPU.')
            else:
                self.get_logger().info('Policy loaded on CPU.')
            with self.lock:
                self.policy = policy
        except Exception as e:
            self.get_logger().error(f'Failed to load policy: {e}')

    def _image_cb(self, msg: Image):
        if self.bridge is None:
            return
        try:
            img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            with self.lock:
                self.latest_image = img
        except Exception as e:
            self.get_logger().warn(f'Image conversion failed: {e}', throttle_duration_sec=5.0)

    def _joint_cb(self, msg: JointState):
        joints = dict(zip(msg.name, msg.position))
        with self.lock:
            self.latest_joints = joints

    def _build_obs(self, image, joints):
        """Build observation dict expected by SmolVLA."""
        # Resize to 512x512
        img = cv2.resize(image, (IMAGE_SIZE, IMAGE_SIZE))
        img_tensor = torch.from_numpy(img).permute(2, 0, 1).float() / 255.0  # (3, H, W)
        img_tensor = img_tensor.unsqueeze(0)  # (1, 3, H, W)

        # Build state: 6 arm joints + 1 gripper
        state = np.zeros(7, dtype=np.float32)
        for i, name in enumerate(ARM_JOINT_NAMES):
            state[i] = joints.get(name, 0.0)
        state[6] = joints.get(GRIPPER_JOINT_NAME, 0.0)
        state_tensor = torch.from_numpy(state).unsqueeze(0)  # (1, 7)

        if torch.cuda.is_available() and next(self.policy.parameters()).is_cuda:
            img_tensor = img_tensor.cuda()
            state_tensor = state_tensor.cuda()

        return {
            'observation.image': img_tensor,
            'observation.state': state_tensor,
            'task': [self.task],
        }

    def _inference_step(self):
        with self.lock:
            policy = self.policy
            image = self.latest_image
            joints = self.latest_joints

        if policy is None:
            return  # Still loading
        if image is None or joints is None:
            return  # Waiting for first observations

        try:
            obs = self._build_obs(image, joints)
            with torch.no_grad():
                # SmolVLA returns action chunk: (1, chunk_size, action_dim)
                actions = policy.select_action(obs)

            actions = actions.cpu().numpy()
            if actions.ndim == 3:
                actions = actions[0]  # (chunk_size, action_dim)
            elif actions.ndim == 1:
                actions = actions[np.newaxis]  # (1, action_dim)

            self._publish_trajectory(actions[:ACTION_CHUNK])

        except Exception as e:
            self.get_logger().error(f'Inference error: {e}', throttle_duration_sec=2.0)

    def _publish_trajectory(self, actions: 'np.ndarray'):
        """
        Publish arm joints from action array.

        actions shape: (N, action_dim) where action_dim >= 6 (arm joints).
        Last dimension index 6 = gripper (ignored here, use gripper_controller separately).
        """
        msg = JointTrajectory()
        msg.joint_names = ARM_JOINT_NAMES
        msg.header.stamp = self.get_clock().now().to_msg()

        for i, action in enumerate(actions):
            pt = JointTrajectoryPoint()
            pt.positions = [float(action[j]) for j in range(6)]
            pt.time_from_start = Duration(
                sec=0,
                nanosec=int(self.step_duration_ms * 1e6 * (i + 1)),
            )
            msg.points.append(pt)

        self.traj_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SmolVLAInferenceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
