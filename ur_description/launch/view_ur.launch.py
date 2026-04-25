# Copyright (c) 2021 PickNik, Inc.
# All rights reserved.

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import (
    Command,
    FindExecutable,
    LaunchConfiguration,
    PathJoinSubstitution,
    PythonExpression,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # Package Configuration
    ur_description_pkg = "ur_description"
    moveit_config_pkg = "moveit_config"

    # Get package share directories
    ur_description_share = FindPackageShare(package=ur_description_pkg).find(ur_description_pkg)
    moveit_config_share = FindPackageShare(package=moveit_config_pkg).find(moveit_config_pkg)

    # File Path Configuration
    urdf_xacro_path = os.path.join(ur_description_share, "urdf", "ur.urdf.xacro")  # Changed to xacro
    urdf_path = os.path.join(moveit_config_share, "config", "ur.urdf")

    srdf_path = os.path.join(moveit_config_share, "config", "ur.srdf.xacro")
    moveit_controllers_path = os.path.join(moveit_config_share, "config", "moveit_controllers.yaml")
    moveit_controllers_onrobot_path = os.path.join(moveit_config_share, "config", "moveit_controllers_onrobot.yaml")
    joint_limits_path = os.path.join(moveit_config_share, "config", "joint_limits.yaml")
    pilz_cartesian_limits_path = os.path.join(moveit_config_share, "config", "pilz_cartesian_limits.yaml")
    rviz_config_path = os.path.join(moveit_config_share, "rviz", "moveit.rviz")  # Use MoveIt config's Rviz
    kinematics_path = os.path.join(moveit_config_share, "config", "kinematics.yaml")

    # Launch Arguments
    declared_arguments = [
        DeclareLaunchArgument(
            "ur_type",
            default_value="ur3",
            description="Type/series of UR robot",
            choices=["ur3", "ur3e", "ur5", "ur5e", "ur10", "ur10e", "ur16e", "ur20", "ur30"],
        ),
        DeclareLaunchArgument(
            "safety_limits",
            default_value="true",
            description="Enable safety limits controller",
        ),
        DeclareLaunchArgument(
            "safety_pos_margin",
            default_value="0.15",
            description="Safety controller position margin",
        ),
        DeclareLaunchArgument(
            "safety_k_position",
            default_value="20",
            description="Safety controller k-position factor",
        ),
        DeclareLaunchArgument(
            "tf_prefix",
            default_value='""',
            description="Prefix for joint names",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock",
        ),
        DeclareLaunchArgument(
            "gripper",
            default_value="robotiq_2f_85",
            description="Gripper to attach to the robot",
            choices=["robotiq_2f_85", "robotiq_2f_140", "onrobot_rg2", "onrobot_rg6"],
        )
    ]

    # Launch Configurations
    ur_type = LaunchConfiguration("ur_type")
    safety_limits = LaunchConfiguration("safety_limits")
    safety_pos_margin = LaunchConfiguration("safety_pos_margin")
    safety_k_position = LaunchConfiguration("safety_k_position")
    tf_prefix = LaunchConfiguration("tf_prefix")
    use_sim_time = LaunchConfiguration("use_sim_time")
    gripper = LaunchConfiguration("gripper")

    # Robot Description (from XACRO)
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            urdf_xacro_path,
            " safety_limits:=", safety_limits,
            " safety_pos_margin:=", safety_pos_margin,
            " safety_k_position:=", safety_k_position,
            " name:=ur",
            " ur_type:=", ur_type,
            " tf_prefix:=", tf_prefix,
            " gripper:=", gripper,
        ]
    )
    robot_description = {"robot_description": ParameterValue(robot_description_content, value_type=str)}

    # MoveIt Configuration
    moveit_config_robotiq = (
        MoveItConfigsBuilder("ur", package_name=moveit_config_pkg)
        .robot_description(file_path=urdf_path)
        .robot_description_semantic(file_path=srdf_path, mappings={"gripper": gripper})
        .joint_limits(file_path=joint_limits_path)
        .robot_description_kinematics(file_path=kinematics_path)
        .pilz_cartesian_limits(file_path=pilz_cartesian_limits_path)
        .planning_pipelines(
            pipelines=["pilz_industrial_motion_planner"],
            default_planning_pipeline="pilz_industrial_motion_planner"
        )
        .trajectory_execution(file_path=moveit_controllers_path)
        .planning_scene_monitor(
            publish_robot_description=True,
            publish_robot_description_semantic=True,
            publish_planning_scene=True
        )
        .to_moveit_configs()
    )
    moveit_config_robotiq.robot_description = robot_description

    moveit_config_onrobot = (
        MoveItConfigsBuilder("ur", package_name=moveit_config_pkg)
        .robot_description(file_path=urdf_path)
        .robot_description_semantic(file_path=srdf_path, mappings={"gripper": gripper})
        .joint_limits(file_path=joint_limits_path)
        .robot_description_kinematics(file_path=kinematics_path)
        .pilz_cartesian_limits(file_path=pilz_cartesian_limits_path)
        .planning_pipelines(
            pipelines=["pilz_industrial_motion_planner"],
            default_planning_pipeline="pilz_industrial_motion_planner"
        )
        .trajectory_execution(file_path=moveit_controllers_onrobot_path)
        .planning_scene_monitor(
            publish_robot_description=True,
            publish_robot_description_semantic=True,
            publish_planning_scene=True
        )
        .to_moveit_configs()
    )
    moveit_config_onrobot.robot_description = robot_description

    # Nodes
    joint_state_publisher_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="both",
        parameters=[robot_description],
    )

    robotiq_condition = IfCondition(
        PythonExpression(["'", gripper, "' in ['robotiq_2f_85', 'robotiq_2f_140']"])
    )
    onrobot_condition = IfCondition(
        PythonExpression(["'", gripper, "' in ['onrobot_rg2', 'onrobot_rg6']"])
    )

    rviz_node_robotiq = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
        parameters=[
            moveit_config_robotiq.robot_description,
            moveit_config_robotiq.robot_description_semantic,
            moveit_config_robotiq.planning_pipelines,
            moveit_config_robotiq.robot_description_kinematics,
            moveit_config_robotiq.joint_limits,
            {"use_sim_time": use_sim_time}
        ],
        condition=robotiq_condition,
    )

    rviz_node_onrobot = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
        parameters=[
            moveit_config_onrobot.robot_description,
            moveit_config_onrobot.robot_description_semantic,
            moveit_config_onrobot.planning_pipelines,
            moveit_config_onrobot.robot_description_kinematics,
            moveit_config_onrobot.joint_limits,
            {"use_sim_time": use_sim_time}
        ],
        condition=onrobot_condition,
    )

    move_group_node_robotiq = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config_robotiq.to_dict()],
        condition=robotiq_condition,
    )

    move_group_node_onrobot = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config_onrobot.to_dict()],
        condition=onrobot_condition,
    )

    return LaunchDescription(
        declared_arguments + [
            joint_state_publisher_node,
            robot_state_publisher_node,
            rviz_node_robotiq,
            rviz_node_onrobot,
            move_group_node_robotiq,
            move_group_node_onrobot,
        ]
    )
