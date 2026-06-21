from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="ur_force_control",
            executable="ft_monitor_node",
            name="ft_monitor_node",
            output="screen",
            parameters=[{
                "effort_threshold": 3.0,
                "close_step": 0.05,
                "step_interval_s": 0.15,
                "max_effort_limit": 8.0,
            }],
        ),
    ])
