"""
Two independent SortingNode instances, one per arm, each filtering
/detected_objects to its own half of the workspace and sorting with its own
MotionExecutor (left_/right_ prefixed joints, left_arm_controller/
right_arm_controller).

Assumes Gazebo + dual-arm move_group are already up
(ur_gazebo dual_ur.gazebo.launch.py). Split line and bin positions are
placeholders (see ur_sorting_demo/config/bins_left.yaml/bins_right.yaml) --
not verified reachable, needs a real dual-arm workspace layout.

Usage:
    ros2 launch ur_sorting_demo dual_sorting_demo.launch.py
    ros2 service call /left/sorting/start std_srvs/srv/Trigger {}
    ros2 service call /right/sorting/start std_srvs/srv/Trigger {}
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    ur_sorting_demo_share = get_package_share_directory("ur_sorting_demo")
    sorting_demo_launch = os.path.join(ur_sorting_demo_share, "launch", "sorting_demo.launch.py")
    bins_left = os.path.join(ur_sorting_demo_share, "config", "bins_left.yaml")
    bins_right = os.path.join(ur_sorting_demo_share, "config", "bins_right.yaml")

    left_sorting = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sorting_demo_launch),
        launch_arguments={
            "namespace": "left",
            "prefix": "left_",
            "params_file": bins_left,
            "enable_workspace_split": "true",
            "split_value": LaunchConfiguration("split_value"),
            "split_keep_positive": "true",
            "min_confidence": LaunchConfiguration("min_confidence"),
            "settle_time": LaunchConfiguration("settle_time"),
        }.items(),
    )

    right_sorting = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sorting_demo_launch),
        launch_arguments={
            "namespace": "right",
            "prefix": "right_",
            "params_file": bins_right,
            "enable_workspace_split": "true",
            "split_value": LaunchConfiguration("split_value"),
            "split_keep_positive": "false",
            "min_confidence": LaunchConfiguration("min_confidence"),
            "settle_time": LaunchConfiguration("settle_time"),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("min_confidence", default_value="0.5"),
        DeclareLaunchArgument("settle_time", default_value="2.0",
                              description="Seconds to wait for perception before starting"),
        DeclareLaunchArgument(
            "split_value", default_value="0.0",
            description="Y-axis workspace split (left keeps y>=split_value, "
                        "right keeps y<split_value) -- TODO: confirm/tune "
                        "against real table geometry"),
        left_sorting,
        right_sorting,
    ])
