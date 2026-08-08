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

    def configure_setup(context):
        """Configure MoveIt and create nodes with proper string conversions."""
        # Get the robot name as a string for use in MoveItConfigsBuilder
        robot_name_str = LaunchConfiguration('robot_name').perform(context)
        gripper_str = gripper.perform(context)

        # Get package path
        pkg_share_moveit_config = pkg_share_moveit_config_temp.find(package_name_moveit_config)
        pkg_share_mtc_pick_place_demo = pkg_share_mtc_pick_place_demo_temp.find(
            package_name_mtc_pick_place_demo)

        # Construct file paths using robot name string
        config_path = os.path.join(pkg_share_moveit_config, 'config')
        mtc_node_config_path = os.path.join(pkg_share_mtc_pick_place_demo, 'config')

        # Define all config file paths
        initial_positions_file_path = os.path.join(config_path, 'initial_positions.yaml')
        joint_limits_file_path = os.path.join(config_path, 'joint_limits.yaml')
        kinematics_file_path = os.path.join(config_path, 'kinematics.yaml')
        if gripper_str in ('onrobot_rg2', 'onrobot_rg6'):
            moveit_controllers_file_path = os.path.join(config_path, 'moveit_controllers_onrobot.yaml')
            mtc_node_params_file_path = os.path.join(mtc_node_config_path, 'mtc_node_params_onrobot.yaml')
        else:
            moveit_controllers_file_path = os.path.join(config_path, 'moveit_controllers.yaml')
            mtc_node_params_file_path = os.path.join(mtc_node_config_path, 'mtc_node_params.yaml')
        srdf_model_path = os.path.join(config_path, 'ur.srdf.xacro')
        pilz_cartesian_limits_file_path = os.path.join(config_path, 'pilz_cartesian_limits.yaml')

        # Create MoveIt configuration
        moveit_config = (
            MoveItConfigsBuilder(robot_name_str, package_name=package_name_moveit_config)
            .trajectory_execution(file_path=moveit_controllers_file_path)
            .robot_description_semantic(file_path=srdf_model_path, mappings={'gripper': gripper})
            .robot_description(file_path=os.path.join(config_path, 'ur.urdf.xacro'), mappings={'gripper': gripper})
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
            output="screen",
            parameters=[
                moveit_config.to_dict(),
                {'use_sim_time': use_sim_time},
                {'start_state': {'content': initial_positions_file_path}},
                mtc_node_params_file_path,
                {'auto_run_on_startup': auto_run_on_startup},
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

    # Add the setup and node creation
    ld.add_action(OpaqueFunction(function=configure_setup))

    return ld
