"""
Launch the RL policy node against the rl_policy_demo.world Gazebo scene.

Usage:
  # Terminal 1 — Gazebo + MoveIt (not strictly required for RL policy, but useful):
  ros2 launch ur_gazebo ur.gazebo.launch.py world_file:=rl_policy_demo.world

  # Terminal 2 — RL policy:
  ros2 launch ur_rl_training rl_policy.launch.py model_path:=<path/to/best_model.zip>

Parameters:
  model_path   — path to the trained .zip model (required)
  object_x/y/z — object position in base_link frame (default: cube centre)
  drop_x/y/z   — drop zone centre in base_link frame
  phase        — starting curriculum phase (0=reach, 1=grasp, 2=lift, 3=place)
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("model_path",  default_value="",    description="Path to SAC model .zip"),
        DeclareLaunchArgument("object_x",    default_value="0.35",description="Object x in base_link frame"),
        DeclareLaunchArgument("object_y",    default_value="0.0", description="Object y in base_link frame"),
        DeclareLaunchArgument("object_z",    default_value="0.045",description="Object z in base_link frame"),
        DeclareLaunchArgument("drop_x",      default_value="0.35",description="Drop zone x"),
        DeclareLaunchArgument("drop_y",      default_value="0.20",description="Drop zone y"),
        DeclareLaunchArgument("drop_z",      default_value="0.02", description="Drop zone z"),
        DeclareLaunchArgument("phase",       default_value="1.0", description="Curriculum phase (0-3)"),
        DeclareLaunchArgument("base_frame",  default_value="base_link"),
        DeclareLaunchArgument("ee_frame",    default_value="tool0"),
        DeclareLaunchArgument("control_rate_hz", default_value="10.0"),

        Node(
            package="ur_rl_training",
            executable="policy_node",
            name="ur3_rl_policy_node",
            output="screen",
            parameters=[{
                "model_path":               LaunchConfiguration("model_path"),
                "object_x":                 LaunchConfiguration("object_x"),
                "object_y":                 LaunchConfiguration("object_y"),
                "object_z":                 LaunchConfiguration("object_z"),
                "drop_x":                   LaunchConfiguration("drop_x"),
                "drop_y":                   LaunchConfiguration("drop_y"),
                "drop_z":                   LaunchConfiguration("drop_z"),
                "phase":                    LaunchConfiguration("phase"),
                "base_frame":               LaunchConfiguration("base_frame"),
                "ee_frame":                 LaunchConfiguration("ee_frame"),
                "control_rate_hz":          LaunchConfiguration("control_rate_hz"),
                "arm_trajectory_topic":     "/arm_controller/joint_trajectory",
                "gripper_trajectory_topic": "/gripper_controller/joint_trajectory",
            }],
        ),
    ])
