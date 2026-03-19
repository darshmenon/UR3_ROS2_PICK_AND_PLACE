"""
Launch file for the ur_perception object detector node.

Usage:
    ros2 launch ur_perception perception.launch.py
    ros2 launch ur_perception perception.launch.py use_yolo:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description() -> LaunchDescription:

    pkg_share = get_package_share_directory('ur_perception')
    default_params_file = os.path.join(pkg_share, 'config', 'detector_params.yaml')

    # ------------------------------------------------------------------ #
    # Launch arguments (allow CLI overrides)
    # ------------------------------------------------------------------ #
    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_params_file,
        description='Full path to the YAML parameter file for the detector node.',
    )

    use_yolo_arg = DeclareLaunchArgument(
        'use_yolo',
        default_value='false',
        description='Enable YOLO-based detection in addition to color detection.',
    )

    # ------------------------------------------------------------------ #
    # Node
    # ------------------------------------------------------------------ #
    object_detector_node = Node(
        package='ur_perception',
        executable='object_detector_node.py',
        name='object_detector_node',
        output='screen',
        parameters=[
            LaunchConfiguration('params_file'),
            {
                # CLI override takes precedence over the YAML file for use_yolo
                'use_yolo': LaunchConfiguration('use_yolo'),
            },
        ],
        remappings=[
            # If your camera namespace differs, remap here:
            # ('/camera_head/color/image_raw', '/your_camera/color/image_raw'),
        ],
    )

    return LaunchDescription([
        params_file_arg,
        use_yolo_arg,
        object_detector_node,
    ])
