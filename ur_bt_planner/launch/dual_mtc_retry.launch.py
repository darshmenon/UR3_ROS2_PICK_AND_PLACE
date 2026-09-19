"""
Two namespaced BT-driven retry wrappers around mtc_node, one per arm.

Layers on top of ur_gazebo dual_ur.gazebo.launch.py the same way
dual_mtc_pick_place.launch.py does, but with each mtc_node's attempts
retried by a namespaced mtc_retry_node (see mtc_retry.launch.py).
force_fallback_scene:true (Phase B decision) means neither instance needs
get_planning_scene_server.

Usage:
    ros2 launch ur_gazebo dual_ur.gazebo.launch.py use_gazebo_gui:=false
    ros2 launch ur_bt_planner dual_mtc_retry.launch.py
    ros2 service call /left/mtc_bt/run std_srvs/srv/Trigger {}
    ros2 service call /right/mtc_bt/run std_srvs/srv/Trigger {}
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    bt_pkg_share = get_package_share_directory("ur_bt_planner")
    mtc_pkg_share = get_package_share_directory("ur_mtc_pick_place_demo")
    mtc_retry_launch = os.path.join(bt_pkg_share, "launch", "mtc_retry.launch.py")
    params_left = os.path.join(mtc_pkg_share, "config", "mtc_node_params_left.yaml")
    params_right = os.path.join(mtc_pkg_share, "config", "mtc_node_params_right.yaml")

    left_retry = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(mtc_retry_launch),
        launch_arguments={
            "namespace": "left",
            "use_dual_arm": "true",
            "gripper": LaunchConfiguration("gripper"),
            "mtc_node_params_file": params_left,
            "include_planning_scene_server": "false",
            "max_attempts": LaunchConfiguration("max_attempts"),
        }.items(),
    )

    right_retry = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(mtc_retry_launch),
        launch_arguments={
            "namespace": "right",
            "use_dual_arm": "true",
            "gripper": LaunchConfiguration("gripper"),
            "mtc_node_params_file": params_right,
            "include_planning_scene_server": "false",
            "max_attempts": LaunchConfiguration("max_attempts"),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "gripper", default_value="robotiq_2f_85",
            description="Gripper to attach to both arms (dual SRDF is "
                        "robotiq-only for now, see Phase A.1)",
            choices=["robotiq_2f_85", "robotiq_2f_140"]),
        DeclareLaunchArgument("max_attempts", default_value="5",
                              description="Pick-place attempts before giving up, per arm"),
        left_retry,
        right_retry,
    ])
