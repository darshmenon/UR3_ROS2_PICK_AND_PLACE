"""
Launch file for the ur_perception policy visualizer node.

Publishes /policy_visualizer/composite_image — a side-by-side [head view with
grasp-confidence heatmap | wrist close-up view] image, seeded from
object_detector_node's /detected_objects.

Usage:
    ros2 launch ur_perception policy_visualizer.launch.py
    # then view with:
    ros2 run rqt_image_view rqt_image_view --ros-args -r image:=/policy_visualizer/composite_image
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    head_color_topic_arg = DeclareLaunchArgument(
        'head_color_topic', default_value='/camera_head/color/image_raw',
    )
    wrist_color_topic_arg = DeclareLaunchArgument(
        'wrist_color_topic', default_value='/camera_wrist/color/image_raw',
    )
    camera_info_topic_arg = DeclareLaunchArgument(
        'camera_info_topic', default_value='/camera_head/camera_info',
    )
    camera_frame_arg = DeclareLaunchArgument(
        'camera_frame', default_value='camera_head_link',
    )
    base_frame_arg = DeclareLaunchArgument(
        'base_frame', default_value='base_link',
    )

    policy_visualizer_node = Node(
        package='ur_perception',
        executable='policy_visualizer_node.py',
        name='policy_visualizer_node',
        output='screen',
        parameters=[{
            'head_color_topic': LaunchConfiguration('head_color_topic'),
            'wrist_color_topic': LaunchConfiguration('wrist_color_topic'),
            'camera_info_topic': LaunchConfiguration('camera_info_topic'),
            'camera_frame': LaunchConfiguration('camera_frame'),
            'base_frame': LaunchConfiguration('base_frame'),
        }],
    )

    return LaunchDescription([
        head_color_topic_arg,
        wrist_color_topic_arg,
        camera_info_topic_arg,
        camera_frame_arg,
        base_frame_arg,
        policy_visualizer_node,
    ])
