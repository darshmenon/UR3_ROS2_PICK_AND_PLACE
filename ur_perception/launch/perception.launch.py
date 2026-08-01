"""
Launch file for the ur_perception object detector node.

Usage:
    ros2 launch ur_perception perception.launch.py
    ros2 launch ur_perception perception.launch.py use_yolo:=true
    # Wrist camera in Gazebo:
    ros2 launch ur_perception perception.launch.py \\
      color_topic:=/camera_wrist/color/image_raw \\
      depth_topic:=/camera_wrist/depth/image_rect_raw \\
      camera_info_topic:=/camera_wrist/camera_info
    # Real Intel RealSense (mm depth):
    ros2 launch ur_perception perception.launch.py \\
      depth_scale:=0.001 \\
      color_topic:=/camera/color/image_raw \\
      depth_topic:=/camera/aligned_depth_to_color/image_raw \\
      camera_info_topic:=/camera/color/camera_info
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:

    pkg_share = get_package_share_directory('ur_perception')
    default_params_file = os.path.join(pkg_share, 'config', 'detector_params.yaml')

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

    color_topic_arg = DeclareLaunchArgument(
        'color_topic',
        default_value='/camera_head/color/image_raw',
    )
    depth_topic_arg = DeclareLaunchArgument(
        'depth_topic',
        default_value='/camera_head/depth/image_rect_raw',
    )
    camera_info_topic_arg = DeclareLaunchArgument(
        'camera_info_topic',
        default_value='/camera_head/camera_info',
    )
    depth_scale_arg = DeclareLaunchArgument(
        'depth_scale',
        default_value='1.0',
        description='1.0 for Gazebo metres; 0.001 for RealSense millimetres',
    )

    object_detector_node = Node(
        package='ur_perception',
        executable='object_detector_node.py',
        name='object_detector_node',
        output='screen',
        parameters=[
            LaunchConfiguration('params_file'),
            {
                'use_yolo': ParameterValue(
                    LaunchConfiguration('use_yolo'), value_type=bool
                ),
                'color_topic': LaunchConfiguration('color_topic'),
                'depth_topic': LaunchConfiguration('depth_topic'),
                'camera_info_topic': LaunchConfiguration('camera_info_topic'),
                'depth_scale': ParameterValue(
                    LaunchConfiguration('depth_scale'), value_type=float
                ),
            },
        ],
    )

    return LaunchDescription([
        params_file_arg,
        use_yolo_arg,
        color_topic_arg,
        depth_topic_arg,
        camera_info_topic_arg,
        depth_scale_arg,
        object_detector_node,
    ])
