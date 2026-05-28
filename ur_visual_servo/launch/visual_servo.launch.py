from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("servo_rate_hz",  default_value="5.0"),
        DeclareLaunchArgument("xy_tolerance",   default_value="0.015"),
        DeclareLaunchArgument("z_tolerance",    default_value="0.010"),
        DeclareLaunchArgument("step_size",      default_value="0.025"),
        DeclareLaunchArgument("grasp_offset_z", default_value="0.05"),
        DeclareLaunchArgument("auto_grasp",     default_value="true"),
        Node(
            package="ur_visual_servo",
            executable="servo_node.py",
            name="visual_servo_node",
            output="screen",
            parameters=[{
                "servo_rate_hz":  LaunchConfiguration("servo_rate_hz"),
                "xy_tolerance":   LaunchConfiguration("xy_tolerance"),
                "z_tolerance":    LaunchConfiguration("z_tolerance"),
                "step_size":      LaunchConfiguration("step_size"),
                "grasp_offset_z": LaunchConfiguration("grasp_offset_z"),
                "auto_grasp":     LaunchConfiguration("auto_grasp"),
            }],
        ),
    ])
