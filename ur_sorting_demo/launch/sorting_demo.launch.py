from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("min_confidence", default_value="0.5"),
        DeclareLaunchArgument("settle_time",    default_value="2.0",
                              description="Seconds to wait for perception before starting"),
        DeclareLaunchArgument("auto_start",     default_value="false",
                              description="Start sorting immediately on launch"),
        Node(
            package="ur_sorting_demo",
            executable="sorting_node.py",
            name="sorting_node",
            output="screen",
            parameters=[{
                "min_confidence": LaunchConfiguration("min_confidence"),
                "settle_time":    LaunchConfiguration("settle_time"),
            }],
        ),
    ])
