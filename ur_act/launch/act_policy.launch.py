from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("model_path",   default_value=""),
        DeclareLaunchArgument("chunk_size",   default_value="10"),
        DeclareLaunchArgument("control_rate_hz", default_value="5.0"),
        DeclareLaunchArgument("temporal_gamma",  default_value="0.01"),
        DeclareLaunchArgument("step_dt_sec",     default_value="0.2"),
        Node(
            package="ur_act",
            executable="act_policy_node",
            name="act_policy_node",
            output="screen",
            parameters=[{
                "model_path":       LaunchConfiguration("model_path"),
                "chunk_size":       LaunchConfiguration("chunk_size"),
                "control_rate_hz":  LaunchConfiguration("control_rate_hz"),
                "temporal_gamma":   LaunchConfiguration("temporal_gamma"),
                "step_dt_sec":      LaunchConfiguration("step_dt_sec"),
            }],
        ),
    ])
