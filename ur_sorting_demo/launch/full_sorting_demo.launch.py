"""
Launch file that brings up the complete multi-object sorting demo in one
command: Gazebo (conveyor world) + move_group, the conveyor belt, object
perception, and the sorting coordinator.

Previously each of these had to be launched by hand in separate terminals,
and the conveyor's own launch file was silently loading the wrong world (see
ur_conveyor/launch/conveyor.launch.py fix). This file only wires the pieces
together; it does not change sorting_node's own logic, which currently reacts
to whatever /detected_objects currently reports rather than to conveyor
arrival events specifically (ur_conveyor/conveyor_node.py's
/conveyor/object_ready topic has no subscriber anywhere yet) -- that's a
separate, larger design decision about whether sorting should be
conveyor-triggered, not something this launch file resolves.

Usage:
    ros2 launch ur_sorting_demo full_sorting_demo.launch.py
    ros2 launch ur_sorting_demo full_sorting_demo.launch.py auto_start:=true
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    ur_conveyor_share = get_package_share_directory("ur_conveyor")
    ur_perception_share = get_package_share_directory("ur_perception")
    ur_sorting_demo_share = get_package_share_directory("ur_sorting_demo")

    return LaunchDescription([
        DeclareLaunchArgument("spawn_interval_s", default_value="6.0"),
        DeclareLaunchArgument("belt_speed",       default_value="0.06"),
        DeclareLaunchArgument("min_confidence",   default_value="0.5"),
        DeclareLaunchArgument("settle_time",      default_value="2.0"),
        DeclareLaunchArgument("auto_start",       default_value="false",
                              description="Start sorting immediately on launch"),

        # Gazebo (conveyor_sorting.world) + move_group + the conveyor belt
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ur_conveyor_share, "launch", "conveyor.launch.py")
            ),
            launch_arguments={
                "spawn_interval_s": LaunchConfiguration("spawn_interval_s"),
                "belt_speed":       LaunchConfiguration("belt_speed"),
            }.items(),
        ),

        # Head-camera object detection -> /detected_objects
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ur_perception_share, "launch", "perception.launch.py")
            ),
        ),

        # Sorting coordinator
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ur_sorting_demo_share, "launch", "sorting_demo.launch.py")
            ),
            launch_arguments={
                "min_confidence": LaunchConfiguration("min_confidence"),
                "settle_time":    LaunchConfiguration("settle_time"),
                "auto_start":     LaunchConfiguration("auto_start"),
            }.items(),
        ),
    ])
