#!/usr/bin/env python3
"""
Launch MoveIt 2 for the handbot robotic arm.

This script creates a ROS 2 launch file that starts the necessary nodes and services
for controlling a handbot robotic arm using MoveIt 2. It loads configuration files,
starts the move_group node, and optionally launches RViz for visualization.

:author: Darsh Menon
:date: December 13, 2024
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler, OpaqueFunction
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_rviz = LaunchConfiguration('use_rviz')
    rviz_config_file = LaunchConfiguration('rviz_config_file')
    rviz_config_package = LaunchConfiguration('rviz_config_package')
    robot_name = LaunchConfiguration('robot_name')
    gripper = LaunchConfiguration('gripper')

    # Package names
    package_name_moveit_config = 'moveit_config'
    package_name_ur_description = 'ur_description'

    # Declare the launch arguments
    declare_robot_name_cmd = DeclareLaunchArgument(
        name='robot_name',
        default_value='ur',
        description='Name of the robot to use')

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name='use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    declare_use_rviz_cmd = DeclareLaunchArgument(
        name='use_rviz',
        default_value='true',
        description='Whether to start RViz')

    declare_use_move_group_cmd = DeclareLaunchArgument(
        name='use_move_group',
        default_value='true',
        description='Whether to start the move_group node (set false for RViz-only)')

    declare_gripper_cmd = DeclareLaunchArgument(
        name='gripper',
        default_value='robotiq_2f_85',
        description='Gripper to attach to the robot',
        choices=['robotiq_2f_85', 'robotiq_2f_140', 'onrobot_rg2', 'onrobot_rg6'])

    declare_rviz_config_file_cmd = DeclareLaunchArgument(
        name='rviz_config_file',
        default_value='moveit.rviz',
        description='RViz configuration file')

    declare_rviz_config_package_cmd = DeclareLaunchArgument(
        name='rviz_config_package',
        default_value=package_name_moveit_config,
        description='Package containing the RViz configuration file')

    def configure_setup(context):
        # Convert robot name from LaunchConfiguration to string
        robot_name_str = robot_name.perform(context)
        gripper_str = gripper.perform(context)

        # Locate package shares
        moveit_config_share = FindPackageShare(package=package_name_moveit_config).find(package_name_moveit_config)

        # File paths from MoveIt config package
        urdf_path_xacro = os.path.join(moveit_config_share, "config", "ur.urdf.xacro")
        srdf_file_path = os.path.join(moveit_config_share, "config", "ur.srdf.xacro")
        joint_limits_file_path = os.path.join(moveit_config_share, "config", "joint_limits.yaml")
        kinematics_file_path = os.path.join(moveit_config_share, "config", "kinematics.yaml")
        pilz_cartesian_limits_file_path = os.path.join(moveit_config_share, "config", "pilz_cartesian_limits.yaml")
        if gripper_str in ("onrobot_rg2", "onrobot_rg6"):
            moveit_controllers_file_path = os.path.join(
                moveit_config_share, "config", "moveit_controllers_onrobot.yaml"
            )
        else:
            moveit_controllers_file_path = os.path.join(
                moveit_config_share, "config", "moveit_controllers.yaml"
            )
        initial_positions_file_path = os.path.join(moveit_config_share, "config", "initial_positions.yaml")

        # Create MoveIt configuration
        moveit_config = (
            MoveItConfigsBuilder(robot_name_str, package_name=package_name_moveit_config)
            .trajectory_execution(file_path=moveit_controllers_file_path)
            .robot_description_semantic(file_path=srdf_file_path, mappings={'gripper': gripper})
            .robot_description(file_path=urdf_path_xacro, mappings={'gripper': gripper})
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

        # MoveIt capabilities
        move_group_capabilities = {"capabilities": "move_group/ExecuteTaskSolutionCapability"}

        # Create move_group node
        start_move_group_node_cmd = Node(
            condition=IfCondition(LaunchConfiguration('use_move_group')),
            package="moveit_ros_move_group",
            executable="move_group",
            output="screen",
            parameters=[
                moveit_config.to_dict(),
                {'use_sim_time': use_sim_time},
                {'start_state': {'content': initial_positions_file_path}},
                move_group_capabilities,
            ],
        )

        # Create RViz node
        start_rviz_node_cmd = Node(
            condition=IfCondition(use_rviz),
            package="rviz2",
            executable="rviz2",
            arguments=[
                "-d",
                [FindPackageShare(rviz_config_package.perform(context)), "/rviz/", rviz_config_file.perform(context)],
            ],
            output="screen",
            parameters=[
                moveit_config.robot_description,
                moveit_config.robot_description_semantic,
                moveit_config.planning_pipelines,
                moveit_config.robot_description_kinematics,
                moveit_config.joint_limits,
                {'use_sim_time': use_sim_time}
            ],
        )

        # Shutdown RViz exits
        exit_event_handler = RegisterEventHandler(
            condition=IfCondition(use_rviz),
            event_handler=OnProcessExit(
                target_action=start_rviz_node_cmd,
                on_exit=EmitEvent(event=Shutdown(reason='RViz exited')),
            ),
        )

        return [start_move_group_node_cmd, start_rviz_node_cmd, exit_event_handler]

    # Create and populate LaunchDescription
    ld = LaunchDescription()

    # Add all arguments
    ld.add_action(declare_robot_name_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(declare_use_move_group_cmd)
    ld.add_action(declare_gripper_cmd)
    ld.add_action(declare_rviz_config_file_cmd)
    ld.add_action(declare_rviz_config_package_cmd)

    # Add node setup
    ld.add_action(OpaqueFunction(function=configure_setup))

    return ld
