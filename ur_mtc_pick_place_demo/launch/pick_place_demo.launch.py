#!/usr/bin/env python3
"""
ROS 2 launch file for the MoveIt Task Constructor pick and place with perception node.

This launch file configures and starts a pick-and-place demo using the MoveIt Task Constructor (MTC)
framework with perception capabilities. It sets up the necessary configurations for
trajectory execution, motion planning, and robot control specifically for the ur platform.

:author: Addison Sears-Collins
:date: December 19, 2024
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    """
    Generate a launch description.

    Returns:
        LaunchDescription: A complete launch description for the MTC pick and place demo system
    """
    # Constants for paths to different files and folders
    package_name_moveit_config = 'moveit_config'
    package_name_mtc_pick_place_demo = 'ur_mtc_pick_place_demo'

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    exe = LaunchConfiguration('exe')
    gripper = LaunchConfiguration('gripper')
    auto_run_on_startup = LaunchConfiguration('auto_run_on_startup')

    # Get the package share directory
    pkg_share_moveit_config_temp = FindPackageShare(package=package_name_moveit_config)
    pkg_share_mtc_pick_place_demo_temp = FindPackageShare(
        package=package_name_mtc_pick_place_demo)

    # Declare the launch arguments
    declare_robot_name_cmd = DeclareLaunchArgument(
        name='robot_name',
        default_value='ur',
        description='Name of the robot to use')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    declare_gripper_cmd = DeclareLaunchArgument(
        name='gripper',
        default_value='robotiq_2f_85',
        description='Gripper to attach to the robot',
        choices=['robotiq_2f_85', 'robotiq_2f_140', 'onrobot_rg2', 'onrobot_rg6'])

    declare_exe_cmd = DeclareLaunchArgument(
        name="exe",
        default_value="mtc_node",
        description="The MoveIt Task Constructor node responsible for pick and place",
        choices=["mtc_node"])

    declare_auto_run_cmd = DeclareLaunchArgument(
        name="auto_run_on_startup",
        default_value="true",
        description="Run one pick-place attempt automatically at launch. Set false when "
                    "a BT (see ur_bt_planner/launch/mtc_retry.launch.py) drives attempts "
                    "via the run_pick_place service instead.")

    # Dual-arm support (see ur_gazebo/launch/dual_mtc_pick_place.launch.py,
    # which includes this file twice with namespace:=left/right). Defaults
    # reproduce single-arm behaviour exactly.
    declare_namespace_cmd = DeclareLaunchArgument(
        name="namespace",
        default_value="",
        description="Node namespace (e.g. 'left'/'right' for dual-arm). Under a "
                    "namespace, run_pick_place resolves to e.g. /left/run_pick_place; "
                    "execute_task_solution is explicitly remapped back to the shared "
                    "/execute_task_solution action server (one move_group serves both "
                    "arms) -- see the remappings on mtc_demo_node below.")

    declare_mtc_node_params_file_cmd = DeclareLaunchArgument(
        name="mtc_node_params_file",
        default_value="",
        description="Override path for mtc_node's params YAML (e.g. "
                    "mtc_node_params_left.yaml). Empty means use the gripper-based "
                    "default (mtc_node_params.yaml / _onrobot.yaml).")

    declare_use_dual_arm_cmd = DeclareLaunchArgument(
        name="use_dual_arm",
        default_value="false",
        description="Build the MoveIt config against the dual-arm robot description "
                    "(dual_ur.srdf.xacro/dual_ur.urdf.xacro/dual_*.yaml) instead of the "
                    "single-arm one, so left_arm/right_arm groups resolve. Required for "
                    "namespace:=left/right use.")

    def configure_setup(context):
        """Configure MoveIt and create nodes with proper string conversions."""
        # Get the robot name as a string for use in MoveItConfigsBuilder
        robot_name_str = LaunchConfiguration('robot_name').perform(context)
        gripper_str = gripper.perform(context)
        namespace_str = LaunchConfiguration('namespace').perform(context)
        mtc_node_params_override = LaunchConfiguration('mtc_node_params_file').perform(context)
        use_dual_arm = LaunchConfiguration('use_dual_arm').perform(context) == 'true'

        # Get package path
        pkg_share_moveit_config = pkg_share_moveit_config_temp.find(package_name_moveit_config)
        pkg_share_mtc_pick_place_demo = pkg_share_mtc_pick_place_demo_temp.find(
            package_name_mtc_pick_place_demo)

        # Construct file paths using robot name string
        config_path = os.path.join(pkg_share_moveit_config, 'config')
        mtc_node_config_path = os.path.join(pkg_share_mtc_pick_place_demo, 'config')

        # Define all config file paths
        initial_positions_file_path = os.path.join(config_path, 'initial_positions.yaml')
        if use_dual_arm:
            # Mirrors ur_gazebo/launch/dual_ur.gazebo.launch.py's
            # MoveItConfigsBuilder("dual_ur", ...) so left_arm/right_arm
            # groups resolve -- the single-arm config below has no such
            # groups.
            joint_limits_file_path = os.path.join(config_path, 'dual_joint_limits.yaml')
            kinematics_file_path = os.path.join(config_path, 'dual_kinematics.yaml')
            moveit_controllers_file_path = os.path.join(config_path, 'dual_moveit_controllers.yaml')
            srdf_model_path = os.path.join(config_path, 'dual_ur.srdf.xacro')
            urdf_model_path = os.path.join(config_path, 'dual_ur.urdf.xacro')
            moveit_config_robot_name = 'dual_ur'
        else:
            joint_limits_file_path = os.path.join(config_path, 'joint_limits.yaml')
            kinematics_file_path = os.path.join(config_path, 'kinematics.yaml')
            if gripper_str in ('onrobot_rg2', 'onrobot_rg6'):
                moveit_controllers_file_path = os.path.join(config_path, 'moveit_controllers_onrobot.yaml')
            else:
                moveit_controllers_file_path = os.path.join(config_path, 'moveit_controllers.yaml')
            srdf_model_path = os.path.join(config_path, 'ur.srdf.xacro')
            urdf_model_path = os.path.join(config_path, 'ur.urdf.xacro')
            moveit_config_robot_name = robot_name_str

        if mtc_node_params_override:
            mtc_node_params_file_path = mtc_node_params_override
        elif gripper_str in ('onrobot_rg2', 'onrobot_rg6'):
            mtc_node_params_file_path = os.path.join(mtc_node_config_path, 'mtc_node_params_onrobot.yaml')
        else:
            mtc_node_params_file_path = os.path.join(mtc_node_config_path, 'mtc_node_params.yaml')
        pilz_cartesian_limits_file_path = os.path.join(config_path, 'pilz_cartesian_limits.yaml')

        # Create MoveIt configuration
        moveit_config = (
            MoveItConfigsBuilder(moveit_config_robot_name, package_name=package_name_moveit_config)
            .trajectory_execution(file_path=moveit_controllers_file_path)
            .robot_description_semantic(file_path=srdf_model_path, mappings={'gripper': gripper})
            .robot_description(file_path=urdf_model_path, mappings={'gripper': gripper})
            .joint_limits(file_path=joint_limits_file_path)
            .robot_description_kinematics(file_path=kinematics_file_path)
            .planning_pipelines(
                pipelines=["ompl", "pilz_industrial_motion_planner"],
                default_planning_pipeline="ompl"
            )
            .planning_scene_monitor(
                publish_robot_description=False,
                publish_robot_description_semantic=True,
                publish_planning_scene=True,
            )
            .pilz_cartesian_limits(file_path=pilz_cartesian_limits_file_path)
            .to_moveit_configs()
        )

        # Create MTC demo node
        mtc_demo_node = Node(
            package="ur_mtc_pick_place_demo",
            executable=exe,
            namespace=namespace_str,
            output="screen",
            parameters=[
                moveit_config.to_dict(),
                {'use_sim_time': use_sim_time},
                {'start_state': {'content': initial_positions_file_path}},
                mtc_node_params_file_path,
                {'auto_run_on_startup': auto_run_on_startup},
            ],
            # execute_task_solution is a relative action client lookup inside
            # mtc_node's executeSolution() -- under a namespace push it would
            # otherwise resolve to /<namespace>/execute_task_solution, but
            # there is only ONE shared move_group (serving every planning
            # group, dual or single-arm) hosting /execute_task_solution.
            # mtc_node.cpp's own get_client/apply_client (lines ~529-530) are
            # already absolute and need no remap -- but
            # moveit::planning_interface::PlanningSceneInterface (constructed
            # internally by mtc_node for ModifyPlanningScene/attach stages)
            # creates its OWN relative "get_planning_scene"/
            # "apply_planning_scene" clients (capability_names.h), which a
            # namespace push would otherwise misroute to
            # /<namespace>/get_planning_scene -- confirmed live: this hung
            # waiting on a nonexistent /left/get_planning_scene service
            # before this remap was added.
            remappings=[
                ('execute_task_solution', '/execute_task_solution'),
                ('get_planning_scene', '/get_planning_scene'),
                ('apply_planning_scene', '/apply_planning_scene'),
            ],
        )

        return [mtc_demo_node]

    # Create the launch description
    ld = LaunchDescription()

    # Add the launch arguments
    ld.add_action(declare_robot_name_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_gripper_cmd)
    ld.add_action(declare_exe_cmd)
    ld.add_action(declare_auto_run_cmd)
    ld.add_action(declare_namespace_cmd)
    ld.add_action(declare_mtc_node_params_file_cmd)
    ld.add_action(declare_use_dual_arm_cmd)

    # Add the setup and node creation
    ld.add_action(OpaqueFunction(function=configure_setup))

    return ld
