"""
point_cloud_viewer.launch.py
Launches a standalone RViz window that shows:
  - Robot model (from /robot_description)
  - Live RGB point cloud  (/camera_head/depth/color/points)
  - Color camera overlay  (/camera_head/color/image_raw)

Assumes the full simulation (ur.gazebo.launch.py) is already running.

Usage
-----
ros2 launch ur_gazebo point_cloud_viewer.launch.py

Optional args:
  rviz_config   path to a custom .rviz file (default: moveit_config/rviz/point_cloud.rviz)
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    moveit_config_share = FindPackageShare("moveit_config").find("moveit_config")
    default_rviz_config = os.path.join(
        moveit_config_share, "rviz", "point_cloud.rviz"
    )

    rviz_config_arg = DeclareLaunchArgument(
        "rviz_config",
        default_value=default_rviz_config,
        description="Path to RViz config file",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="point_cloud_rviz",
        arguments=["-d", LaunchConfiguration("rviz_config")],
        output="screen",
        additional_env={"DISPLAY": os.environ.get("DISPLAY", ":0")},
    )

    return LaunchDescription([
        rviz_config_arg,
        rviz_node,
    ])
