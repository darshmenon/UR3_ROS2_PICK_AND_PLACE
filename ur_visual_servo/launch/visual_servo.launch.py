from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("servo_rate_hz",  default_value="5.0"),
        # 0.015 (1.5cm) let the loop "converge" up to 1.5cm off-center — enough
        # for one finger to clip a small object (~4cm) instead of centering on
        # it. 0.006 keeps convergence well inside typical object radii.
        DeclareLaunchArgument("xy_tolerance",   default_value="0.006"),
        DeclareLaunchArgument("z_tolerance",    default_value="0.010"),
        DeclareLaunchArgument("step_size",      default_value="0.025"),
        DeclareLaunchArgument("grasp_offset_z", default_value="0.05"),
        DeclareLaunchArgument("auto_grasp",     default_value="true"),
        DeclareLaunchArgument("ee_frame",       default_value="tool0"),
        DeclareLaunchArgument("gripper_joint_name",   default_value="finger_joint",
                              description="Use gripper_joint for OnRobot RG2/RG6"),
        DeclareLaunchArgument("gripper_fully_closed", default_value="0.8",
                              description="1.3 for OnRobot RG2/RG6"),
        DeclareLaunchArgument("gripper_stall_margin", default_value="0.05"),
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
                "gripper_joint_name":   LaunchConfiguration("gripper_joint_name"),
                "gripper_fully_closed": ParameterValue(
                    LaunchConfiguration("gripper_fully_closed"), value_type=float
                ),
                "gripper_stall_margin": ParameterValue(
                    LaunchConfiguration("gripper_stall_margin"), value_type=float
                ),
            }],
        ),
    ])
