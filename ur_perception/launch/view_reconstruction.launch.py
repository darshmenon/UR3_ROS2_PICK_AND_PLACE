"""
view_reconstruction.launch.py — load a saved PLY (written by
object_reconstructor_node's save_path/reconstruct/stop) into RViz.

Usage:
  ros2 launch ur_perception view_reconstruction.launch.py ply_path:=/tmp/object.ply
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory("ur_perception")
    default_rviz_config = os.path.join(pkg_share, "rviz", "reconstruction.rviz")

    return LaunchDescription([
        DeclareLaunchArgument(
            "ply_path", default_value="",
            description="Path to the ASCII PLY to load (required — from "
                        "object_reconstructor_node's save_path)",
        ),
        DeclareLaunchArgument(
            "frame_id", default_value="base_link",
            description="Frame to publish the loaded cloud in",
        ),
        DeclareLaunchArgument(
            "rviz_config", default_value=default_rviz_config,
            description="RViz config file — defaults to this package's own, "
                        "resolved via its install share dir (no hardcoded path)",
        ),
        DeclareLaunchArgument(
            "use_rviz", default_value="true",
            description="Launch RViz alongside the publisher",
        ),

        Node(
            package="ur_perception",
            executable="ply_viewer_node.py",
            name="ply_viewer_node",
            output="screen",
            parameters=[{
                "ply_path": LaunchConfiguration("ply_path"),
                "frame_id": LaunchConfiguration("frame_id"),
            }],
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            output="screen",
            arguments=["-d", LaunchConfiguration("rviz_config")],
            condition=IfCondition(LaunchConfiguration("use_rviz")),
        ),
    ])
