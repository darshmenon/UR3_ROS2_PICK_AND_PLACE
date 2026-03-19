#!/usr/bin/env python3
"""
DataCollectorNode - Records robot demonstrations for behavior cloning and VLA fine-tuning.

Subscribes to joint states and camera topics, buffers data while recording,
and saves episodes to HDF5 files on demand via service calls.
"""

import os
import time
import threading
from datetime import datetime

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import JointState, Image
from std_srvs.srv import Trigger

try:
    from cv_bridge import CvBridge
    CV_BRIDGE_AVAILABLE = True
except ImportError:
    CV_BRIDGE_AVAILABLE = False

try:
    import h5py
    H5PY_AVAILABLE = True
except ImportError:
    H5PY_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# Arm joint names for the UR3
ARM_JOINT_NAMES = [
    'shoulder_pan_joint',
    'shoulder_lift_joint',
    'elbow_joint',
    'wrist_1_joint',
    'wrist_2_joint',
    'wrist_3_joint',
]

# Gripper joint name
GRIPPER_JOINT_NAME = 'finger_joint'


class DataCollectorNode(Node):
    """
    Records robot demonstrations to HDF5 files.

    Start a recording episode with /data_collector/start_recording (std_srvs/Trigger).
    Stop and save with /data_collector/stop_recording (std_srvs/Trigger).
    """

    def __init__(self):
        super().__init__('data_collector_node')

        # ------------------------------------------------------------------
        # Parameters
        # ------------------------------------------------------------------
        self.declare_parameter('output_dir', '~/ur3_demos')
        self.declare_parameter('image_height', 240)
        self.declare_parameter('image_width', 424)
        self.declare_parameter('record_depth', True)
        self.declare_parameter('episode_name_prefix', 'demo')

        self.output_dir = os.path.expanduser(
            self.get_parameter('output_dir').get_parameter_value().string_value
        )
        self.image_height = self.get_parameter('image_height').get_parameter_value().integer_value
        self.image_width = self.get_parameter('image_width').get_parameter_value().integer_value
        self.record_depth = self.get_parameter('record_depth').get_parameter_value().bool_value
        self.episode_name_prefix = (
            self.get_parameter('episode_name_prefix').get_parameter_value().string_value
        )

        os.makedirs(self.output_dir, exist_ok=True)

        # ------------------------------------------------------------------
        # Internal state
        # ------------------------------------------------------------------
        self._recording = False
        self._lock = threading.Lock()

        # Episode buffers
        self._timestamps: list = []
        self._joint_positions: list = []       # (6,) arm joints
        self._gripper_positions: list = []     # (1,) gripper
        self._rgb_images: list = []            # (H, W, 3) uint8
        self._depth_images: list = []          # (H, W) float32

        # Latest sensor data (thread-safe via lock)
        self._latest_joint_positions = None    # np.ndarray shape (6,)
        self._latest_gripper_position = None   # float
        self._latest_rgb = None                # np.ndarray (H, W, 3) uint8
        self._latest_depth = None              # np.ndarray (H, W) float32

        # CV bridge for image conversion
        if CV_BRIDGE_AVAILABLE:
            self._bridge = CvBridge()
        else:
            self._bridge = None
            self.get_logger().warn(
                'cv_bridge not available. Image recording will be disabled.'
            )

        if not H5PY_AVAILABLE:
            self.get_logger().warn(
                'h5py not available. Install with: pip3 install h5py\n'
                'Saving to HDF5 will fail.'
            )

        if not NUMPY_AVAILABLE:
            self.get_logger().error('numpy not available. This node requires numpy.')

        # ------------------------------------------------------------------
        # QoS profile for sensor topics
        # ------------------------------------------------------------------
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # ------------------------------------------------------------------
        # Subscriptions
        # ------------------------------------------------------------------
        self._joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self._joint_state_callback,
            10,
        )

        self._rgb_sub = self.create_subscription(
            Image,
            '/camera_head/color/image_raw',
            self._rgb_callback,
            sensor_qos,
        )

        self._depth_sub = self.create_subscription(
            Image,
            '/camera_head/depth/image_rect_raw',
            self._depth_callback,
            sensor_qos,
        )

        # ------------------------------------------------------------------
        # Services
        # ------------------------------------------------------------------
        self._start_srv = self.create_service(
            Trigger,
            '/data_collector/start_recording',
            self._start_recording_callback,
        )

        self._stop_srv = self.create_service(
            Trigger,
            '/data_collector/stop_recording',
            self._stop_recording_callback,
        )

        # ------------------------------------------------------------------
        # Timer for buffering at ~5 Hz
        # ------------------------------------------------------------------
        self._buffer_timer = self.create_timer(0.2, self._buffer_callback)

        self.get_logger().info(
            f'DataCollectorNode ready. Output dir: {self.output_dir}\n'
            f'  Start: ros2 service call /data_collector/start_recording std_srvs/srv/Trigger\n'
            f'  Stop:  ros2 service call /data_collector/stop_recording  std_srvs/srv/Trigger'
        )

    # ------------------------------------------------------------------
    # Subscription callbacks
    # ------------------------------------------------------------------

    def _joint_state_callback(self, msg: JointState):
        """Extract arm and gripper joint positions from JointState message."""
        if not NUMPY_AVAILABLE:
            return

        import numpy as np

        name_to_pos = dict(zip(msg.name, msg.position))

        # Extract arm joints (6 DOF), defaulting to 0.0 if not present
        arm_positions = np.array(
            [name_to_pos.get(j, 0.0) for j in ARM_JOINT_NAMES],
            dtype=np.float32,
        )

        # Extract gripper (single value)
        gripper_pos = float(name_to_pos.get(GRIPPER_JOINT_NAME, 0.0))

        with self._lock:
            self._latest_joint_positions = arm_positions
            self._latest_gripper_position = gripper_pos

    def _rgb_callback(self, msg: Image):
        """Convert incoming RGB image to numpy array."""
        if not CV_BRIDGE_AVAILABLE or self._bridge is None:
            return
        if not NUMPY_AVAILABLE:
            return

        import numpy as np

        try:
            cv_image = self._bridge.imgmsg_to_cv2(msg, desired_encoding='rgb8')
            # Resize if needed
            if (cv_image.shape[0] != self.image_height or
                    cv_image.shape[1] != self.image_width):
                try:
                    import cv2
                    cv_image = cv2.resize(
                        cv_image,
                        (self.image_width, self.image_height),
                        interpolation=cv2.INTER_LINEAR,
                    )
                except ImportError:
                    pass  # Keep original size if cv2 not available

            with self._lock:
                self._latest_rgb = np.array(cv_image, dtype=np.uint8)
        except Exception as e:
            self.get_logger().warn(f'RGB image conversion failed: {e}', throttle_duration_sec=5.0)

    def _depth_callback(self, msg: Image):
        """Convert incoming depth image to float32 numpy array in meters."""
        if not CV_BRIDGE_AVAILABLE or self._bridge is None:
            return
        if not NUMPY_AVAILABLE:
            return
        if not self.record_depth:
            return

        import numpy as np

        try:
            # Depth images are typically 16UC1 (millimeters) or 32FC1 (meters)
            if msg.encoding == '32FC1':
                cv_image = self._bridge.imgmsg_to_cv2(msg, desired_encoding='32FC1')
            else:
                # 16UC1 → convert mm to meters
                cv_image = self._bridge.imgmsg_to_cv2(msg, desired_encoding='16UC1')
                cv_image = cv_image.astype(np.float32) / 1000.0

            # Resize if needed
            if (cv_image.shape[0] != self.image_height or
                    cv_image.shape[1] != self.image_width):
                try:
                    import cv2
                    cv_image = cv2.resize(
                        cv_image,
                        (self.image_width, self.image_height),
                        interpolation=cv2.INTER_NEAREST,
                    )
                except ImportError:
                    pass

            with self._lock:
                self._latest_depth = np.array(cv_image, dtype=np.float32)
        except Exception as e:
            self.get_logger().warn(f'Depth image conversion failed: {e}', throttle_duration_sec=5.0)

    # ------------------------------------------------------------------
    # Buffer timer callback (5 Hz)
    # ------------------------------------------------------------------

    def _buffer_callback(self):
        """Append current sensor readings to episode buffers when recording."""
        if not self._recording:
            return
        if not NUMPY_AVAILABLE:
            return

        import numpy as np

        with self._lock:
            joint_pos = self._latest_joint_positions
            gripper_pos = self._latest_gripper_position
            rgb = self._latest_rgb
            depth = self._latest_depth

        # Need at least joint state data to record a step
        if joint_pos is None:
            return

        timestamp = self.get_clock().now().nanoseconds * 1e-9  # seconds

        self._timestamps.append(timestamp)
        self._joint_positions.append(joint_pos.copy())
        self._gripper_positions.append(
            np.array([gripper_pos if gripper_pos is not None else 0.0], dtype=np.float32)
        )

        # RGB image: use zeros if not available
        if rgb is not None:
            self._rgb_images.append(rgb.copy())
        else:
            self._rgb_images.append(
                np.zeros((self.image_height, self.image_width, 3), dtype=np.uint8)
            )

        # Depth image: use zeros if not available or not recording depth
        if self.record_depth:
            if depth is not None:
                self._depth_images.append(depth.copy())
            else:
                self._depth_images.append(
                    np.zeros((self.image_height, self.image_width), dtype=np.float32)
                )

    # ------------------------------------------------------------------
    # Service callbacks
    # ------------------------------------------------------------------

    def _start_recording_callback(self, request, response):
        """Begin a new recording episode."""
        if self._recording:
            response.success = False
            response.message = 'Already recording. Stop the current episode first.'
            return response

        # Clear buffers
        self._timestamps.clear()
        self._joint_positions.clear()
        self._gripper_positions.clear()
        self._rgb_images.clear()
        self._depth_images.clear()

        self._recording = True
        self._episode_start_time = time.time()

        self.get_logger().info('Recording started.')
        response.success = True
        response.message = 'Recording started.'
        return response

    def _stop_recording_callback(self, request, response):
        """End the current episode and save to HDF5."""
        if not self._recording:
            response.success = False
            response.message = 'Not currently recording.'
            return response

        self._recording = False
        duration = time.time() - self._episode_start_time
        num_steps = len(self._timestamps)

        self.get_logger().info(
            f'Recording stopped. Steps: {num_steps}, Duration: {duration:.1f}s'
        )

        if num_steps == 0:
            response.success = False
            response.message = 'No data recorded (0 steps). Episode not saved.'
            return response

        # Save in a background thread so we don't block the service response
        save_thread = threading.Thread(
            target=self._save_episode,
            args=(
                list(self._timestamps),
                list(self._joint_positions),
                list(self._gripper_positions),
                list(self._rgb_images),
                list(self._depth_images),
                num_steps,
                duration,
            ),
            daemon=True,
        )
        save_thread.start()

        response.success = True
        response.message = f'Episode stopped ({num_steps} steps, {duration:.1f}s). Saving...'
        return response

    # ------------------------------------------------------------------
    # HDF5 save
    # ------------------------------------------------------------------

    def _save_episode(
        self,
        timestamps,
        joint_positions,
        gripper_positions,
        rgb_images,
        depth_images,
        num_steps,
        duration,
    ):
        """Save episode buffers to an HDF5 file."""
        if not H5PY_AVAILABLE:
            self.get_logger().error(
                'h5py not installed. Cannot save episode.\n'
                'Install with: pip3 install h5py'
            )
            return

        if not NUMPY_AVAILABLE:
            self.get_logger().error('numpy not available. Cannot save episode.')
            return

        import numpy as np

        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(
            self.output_dir,
            f'{self.episode_name_prefix}_{timestamp_str}.h5',
        )

        try:
            ts_arr = np.array(timestamps, dtype=np.float64)                       # (N,)
            jp_arr = np.stack(joint_positions, axis=0).astype(np.float32)         # (N, 6)
            gp_arr = np.stack(gripper_positions, axis=0).astype(np.float32)       # (N, 1)
            rgb_arr = np.stack(rgb_images, axis=0).astype(np.uint8)               # (N, H, W, 3)

            # Actions: joint positions + gripper (for behavior cloning supervision)
            actions_arr = np.concatenate([jp_arr, gp_arr], axis=1).astype(np.float32)  # (N, 7)

            with h5py.File(filename, 'w') as f:
                f.create_dataset('timestamps', data=ts_arr, compression='gzip')
                f.create_dataset('joint_positions', data=jp_arr, compression='gzip')
                f.create_dataset('gripper_positions', data=gp_arr, compression='gzip')
                f.create_dataset(
                    'rgb_images',
                    data=rgb_arr,
                    compression='gzip',
                    compression_opts=4,
                )
                f.create_dataset('actions', data=actions_arr, compression='gzip')

                if self.record_depth and len(depth_images) == num_steps:
                    depth_arr = np.stack(depth_images, axis=0).astype(np.float32)  # (N, H, W)
                    f.create_dataset(
                        'depth_images',
                        data=depth_arr,
                        compression='gzip',
                        compression_opts=4,
                    )

                # Metadata attributes
                f.attrs['num_steps'] = num_steps
                f.attrs['duration_s'] = duration
                f.attrs['image_height'] = self.image_height
                f.attrs['image_width'] = self.image_width
                f.attrs['arm_joint_names'] = ARM_JOINT_NAMES
                f.attrs['gripper_joint_name'] = GRIPPER_JOINT_NAME

            self.get_logger().info(
                f'Episode saved to: {filename}\n'
                f'  Steps: {num_steps}, Duration: {duration:.1f}s, '
                f'RGB shape: {rgb_arr.shape}'
            )

        except Exception as e:
            self.get_logger().error(f'Failed to save episode: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = DataCollectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
