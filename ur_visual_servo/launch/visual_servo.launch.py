from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("servo_rate_hz",  default_value="5.0"),
        DeclareLaunchArgument("xy_tolerance",   default_value="0.015"),
        DeclareLaunchArgument("z_tolerance",    default_value="0.010"),
        DeclareLaunchArgument("step_size",      default_value="0.025"),
        DeclareLaunchArgument("grasp_offset_z", default_value="0.05"),
        DeclareLaunchArgument("auto_grasp",     default_value="true"),
        DeclareLaunchArgument("ee_frame",       default_value="tool0"),
        Node(
            package="ur_visual_servo",
            executable="servo_node.py",
            name="visual_servo_node",
            output="screen",
            parameters=[{
                "servo_rate_hz":  ParameterValue(
                    LaunchConfiguration("servo_rate_hz"), value_type=float
                ),
                "xy_tolerance":   ParameterValue(
                    LaunchConfiguration("xy_tolerance"), value_type=float
                ),
                "z_tolerance":    ParameterValue(
                    LaunchConfiguration("z_tolerance"), value_type=float
                ),
                "step_size":      ParameterValue(
                    LaunchConfiguration("step_size"), value_type=float
                ),
                "grasp_offset_z": ParameterValue(
                    LaunchConfiguration("grasp_offset_z"), value_type=float
                ),
                "auto_grasp":     ParameterValue(
                    LaunchConfiguration("auto_grasp"), value_type=bool
                ),
                "ee_frame":       LaunchConfiguration("ee_frame"),
                # tcp_offset_xyz defaults in the node to [0, 0, 0.145] (2F-85).
                # Override with: ros2 param set /visual_servo_node tcp_offset_xyz "[0.0, 0.0, 0.145]"
            }],
        ),
    ])
