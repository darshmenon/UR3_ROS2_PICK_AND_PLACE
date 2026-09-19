"""
Two namespaced instances of ur_mtc_pick_place_demo's mtc_node, one per arm,
each built against the dual-arm MoveIt config (left_arm/right_arm groups)
with force_fallback_scene:true (no live perception dependency -- see
mtc_node_params_left.yaml/_right.yaml TODO placeholders for the hardcoded
object/place geometry, not yet verified reachable).

Assumes Gazebo + dual-arm move_group are already up
(ur_gazebo dual_ur.gazebo.launch.py). auto_run_on_startup is false for both
-- trigger attempts via /left/run_pick_place, /right/run_pick_place
(std_srvs/Trigger), or layer ur_bt_planner's dual_mtc_retry.launch.py on top
for BT-driven retries.

Usage:
    ros2 launch ur_gazebo dual_ur.gazebo.launch.py use_gazebo_gui:=false
    ros2 launch ur_gazebo dual_mtc_pick_place.launch.py
    ros2 service call /left/run_pick_place std_srvs/srv/Trigger {}
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    mtc_pkg_share = get_package_share_directory("ur_mtc_pick_place_demo")
    pick_place_launch = os.path.join(mtc_pkg_share, "launch", "pick_place_demo.launch.py")
    params_left = os.path.join(mtc_pkg_share, "config", "mtc_node_params_left.yaml")
    params_right = os.path.join(mtc_pkg_share, "config", "mtc_node_params_right.yaml")

    left_mtc = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(pick_place_launch),
        launch_arguments={
            "namespace": "left",
            "use_dual_arm": "true",
            "gripper": LaunchConfiguration("gripper"),
            "mtc_node_params_file": params_left,
            "auto_run_on_startup": "false",
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }.items(),
    )

    right_mtc = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(pick_place_launch),
        launch_arguments={
            "namespace": "right",
            "use_dual_arm": "true",
            "gripper": LaunchConfiguration("gripper"),
            "mtc_node_params_file": params_right,
            "auto_run_on_startup": "false",
            "use_sim_time": LaunchConfiguration("use_sim_time"),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "gripper", default_value="robotiq_2f_85",
            description="Gripper to attach to both arms (dual SRDF is "
                        "robotiq-only for now, see Phase A.1)",
            choices=["robotiq_2f_85", "robotiq_2f_140"]),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        left_mtc,
        right_mtc,
    ])
