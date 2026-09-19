"""
BT-driven retry wrapper for the MTC pick-and-place pipeline.

Assumes Gazebo + move_group are already up (ur_gazebo ur.gazebo.launch.py).
Starts get_planning_scene_server (unless disabled) + mtc_node
(auto_run_on_startup:=false, so only the BT triggers attempts, not
mtc_node's own startup) + mtc_retry_node.

After launch, call:
    ros2 service call /mtc_bt/run std_srvs/srv/Trigger {}
(or /<namespace>/mtc_bt/run under a namespace) and watch /mtc_bt/status
(or /<namespace>/mtc_bt/status) for progress.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    gripper = LaunchConfiguration("gripper")
    max_attempts = LaunchConfiguration("max_attempts")
    namespace = LaunchConfiguration("namespace")

    get_planning_scene_server_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("ur_mtc_pick_place_demo"),
                "launch",
                "get_planning_scene_server.launch.py",
            ])
        ),
        # Dual-arm instances default force_fallback_scene:true (no live
        # perception dependency, see Phase B decision) and don't need this
        # server; single-arm use keeps it on by default.
        condition=IfCondition(LaunchConfiguration("include_planning_scene_server")),
    )

    mtc_node_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare("ur_mtc_pick_place_demo"),
                "launch",
                "pick_place_demo.launch.py",
            ])
        ),
        launch_arguments={
            "gripper": gripper,
            "auto_run_on_startup": "false",
            "namespace": namespace,
            "mtc_node_params_file": LaunchConfiguration("mtc_node_params_file"),
            "use_dual_arm": LaunchConfiguration("use_dual_arm"),
        }.items(),
    )

    mtc_retry_node = Node(
        package="ur_bt_planner",
        executable="mtc_retry_node.py",
        name="mtc_retry_node",
        namespace=namespace,
        output="screen",
        parameters=[{
            "max_attempts": max_attempts,
        }],
    )

    return LaunchDescription([
        DeclareLaunchArgument("gripper", default_value="robotiq_2f_85",
                              description="Gripper to attach to the robot"),
        DeclareLaunchArgument("max_attempts", default_value="5",
                              description="Pick-place attempts before giving up"),
        # Dual-arm support (see dual_mtc_retry.launch.py). Defaults
        # reproduce single-arm behaviour exactly.
        DeclareLaunchArgument("namespace", default_value="",
                              description="Node namespace (e.g. 'left'/'right' for dual-arm)"),
        DeclareLaunchArgument("mtc_node_params_file", default_value="",
                              description="Override path for mtc_node's params YAML"),
        DeclareLaunchArgument("use_dual_arm", default_value="false",
                              description="Build MoveIt config against the dual-arm robot description"),
        DeclareLaunchArgument("include_planning_scene_server", default_value="true",
                              description="Start get_planning_scene_server (skip for "
                                          "force_fallback_scene:true dual-arm use)"),
        get_planning_scene_server_launch,
        mtc_node_launch,
        mtc_retry_node,
    ])
