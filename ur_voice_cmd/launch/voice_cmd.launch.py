from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("backend",      default_value="auto",
                              description="STT backend: auto|whisper|google|sphinx"),
        DeclareLaunchArgument("whisper_model", default_value="base",
                              description="faster-whisper model size: tiny|base|small|medium|large"),
        DeclareLaunchArgument("language",     default_value="en"),
        DeclareLaunchArgument("energy_threshold", default_value="300"),
        Node(
            package="ur_voice_cmd",
            executable="voice_cmd_node.py",
            name="voice_cmd_node",
            output="screen",
            parameters=[{
                "backend":          LaunchConfiguration("backend"),
                "whisper_model":    LaunchConfiguration("whisper_model"),
                "language":         LaunchConfiguration("language"),
                "energy_threshold": LaunchConfiguration("energy_threshold"),
            }],
        ),
    ])
