"""
Launch Gazebo simulation with a UR robot.

This launch file sets up a complete ROS 2 simulation environment with Gazebo.
"""

import os
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    GroupAction,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.conditions import UnlessCondition
from launch.event_handlers import OnProcessStart
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    """
    Generate a launch description for the Gazebo simulation.
    """
    # Package names
    package_name_gazebo = 'ur_gazebo'
    package_name_description = 'ur_description'
    package_name_moveit = 'moveit_config'

    # Default values
    default_robot_name = 'ur'
    default_world_file = 'colored_blocks.world'
    gazebo_models_path = 'models'
    gazebo_worlds_path = 'worlds'
    ros_gz_bridge_config_file_path = 'config/ros_gz_bridge.yaml'
    ur_description_pkg = "ur_description"
    moveit_config_pkg = "moveit_config"

    # Get package share directories
    ur_description_share = FindPackageShare(package=ur_description_pkg).find(ur_description_pkg)
    moveit_config_share = FindPackageShare(package=moveit_config_pkg).find(moveit_config_pkg)

    # File Path Configuration
    srdf_path = os.path.join(moveit_config_share, "config", "ur.srdf.xacro")
    moveit_controllers_path = os.path.join(moveit_config_share, "config", "moveit_controllers.yaml")
    moveit_controllers_onrobot_path = os.path.join(moveit_config_share, "config", "moveit_controllers_onrobot.yaml")
    joint_limits_path = os.path.join(moveit_config_share, "config", "joint_limits.yaml")
    pilz_cartesian_limits_path = os.path.join(moveit_config_share, "config", "pilz_cartesian_limits.yaml")
    rviz_config_path = os.path.join(moveit_config_share, "rviz", "moveit.rviz")
    kinematics_path = os.path.join(moveit_config_share, "config", "kinematics.yaml")
    
    # Find package paths
    pkg_ros_gz_sim = FindPackageShare('ros_gz_sim').find('ros_gz_sim')
    pkg_share_gazebo = FindPackageShare(package_name_gazebo).find(package_name_gazebo)
    pkg_share_description = FindPackageShare(package_name_description).find(package_name_description)
    pkg_share_moveit = FindPackageShare(package_name_moveit).find(package_name_moveit)

    # Ensure the locally-built gz_ros2_control (compiled for Gazebo Harmonic) is found
    # before the apt-installed version (which was compiled for Ignition Fortress).
    local_gz_plugin_path = FindPackageShare('gz_ros2_control').find('gz_ros2_control')
    local_gz_plugin_lib = os.path.join(os.path.dirname(local_gz_plugin_path), '..', 'lib')

    # Set paths
    gazebo_models_path = os.path.join(pkg_share_gazebo, gazebo_models_path)
    default_ros_gz_bridge_config_file_path = os.path.join(pkg_share_gazebo, ros_gz_bridge_config_file_path)

    # Launch Configurations
    world_file = LaunchConfiguration('world_file')
    world_path = PathJoinSubstitution([pkg_share_gazebo, gazebo_worlds_path, world_file])
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')
    gripper = LaunchConfiguration('gripper')

    # Declare launch arguments
    declared_arguments = [
        DeclareLaunchArgument("robot_name", default_value=default_robot_name, description="The name for the robot"),
        DeclareLaunchArgument("use_sim_time", default_value="true", description="Use simulation (Gazebo) clock if true"),
        DeclareLaunchArgument("world_file", default_value=default_world_file, description="World file name"),
        DeclareLaunchArgument("ur_type", default_value="ur3", description="Type/series of UR robot",
                              choices=["ur3", "ur3e", "ur5", "ur5e", "ur10", "ur10e", "ur16e", "ur20", "ur30"]),
        DeclareLaunchArgument(
            "gripper",
            default_value="robotiq_2f_85",
            description="Gripper to attach to the robot",
            choices=["robotiq_2f_85", "robotiq_2f_140", "onrobot_rg2", "onrobot_rg6"],
        ),
        DeclareLaunchArgument("safety_limits", default_value="true", description="Enable safety limits controller"),
        DeclareLaunchArgument("safety_pos_margin", default_value="0.15", description="Safety controller position margin"),
        DeclareLaunchArgument("safety_k_position", default_value="20", description="Safety controller k-position factor"),
        DeclareLaunchArgument("tf_prefix", default_value='""', description="Prefix for joint names"),
        DeclareLaunchArgument("use_rviz", default_value="true", description="Launch RViz2"),
        DeclareLaunchArgument("use_move_group", default_value="true", description="Launch move_group node"),
        DeclareLaunchArgument("use_gazebo_gui", default_value="true", description="Launch Gazebo with the GUI client"),
    ]

    # Create launch description
    ld = LaunchDescription(declared_arguments)

    # Prepend local gz_ros2_control lib (Harmonic build) to GZ_SIM_SYSTEM_PLUGIN_PATH
    ld.add_action(AppendEnvironmentVariable(
        'GZ_SIM_SYSTEM_PLUGIN_PATH',
        local_gz_plugin_lib,
        prepend=True,
    ))
    
    # Use pkg_share_description for the URDF xacro file
    urdf_xacro_path = os.path.join(moveit_config_share, "config", "ur.urdf.xacro")

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        urdf_xacro_path,
        " ",
        "gripper:=",
        gripper,
    ])

    robot_description = {'robot_description': ParameterValue(robot_description_content, value_type=str)}


    joint_state_publisher_node = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
    )
    # Robot State Publisher
    robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='both',
        parameters=[robot_description, {'use_sim_time': use_sim_time}]
    )

    start_gazebo_ros_bridge_cmd = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': default_ros_gz_bridge_config_file_path,
        }],
        output='screen'
    )

    # MoveIt Configuration
    moveit_config_robotiq = (
        MoveItConfigsBuilder("ur", package_name=moveit_config_pkg)
        .trajectory_execution(file_path=moveit_controllers_path)
        .robot_description_semantic(file_path=srdf_path, mappings={'gripper': gripper})
        .joint_limits(file_path=joint_limits_path)
        .robot_description_kinematics(file_path=kinematics_path)
        .pilz_cartesian_limits(file_path=pilz_cartesian_limits_path)
        .planning_pipelines(
        pipelines=["ompl", "pilz_industrial_motion_planner"],
        default_planning_pipeline="ompl"
     )
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
        .trajectory_execution(file_path=moveit_controllers_onrobot_path)
        .robot_description_semantic(file_path=srdf_path, mappings={'gripper': gripper})
        .joint_limits(file_path=joint_limits_path)
        .robot_description_kinematics(file_path=kinematics_path)
        .pilz_cartesian_limits(file_path=pilz_cartesian_limits_path)
        .planning_pipelines(
        pipelines=["ompl", "pilz_industrial_motion_planner"],
        default_planning_pipeline="ompl"
     )
        .planning_scene_monitor(
            publish_robot_description=True,
            publish_robot_description_semantic=True,
            publish_planning_scene=True
        )
        .to_moveit_configs()
      )
    moveit_config_onrobot.robot_description = robot_description

    # Set environment variables
    set_env_vars_resources = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        gazebo_models_path
    )

    # load_controllers_cmd = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource([
    #         os.path.join(pkg_share_moveit, 'launch', 'load_ros2_controllers.launch.py')
    #     ]),
    #     launch_arguments={
    #         'use_sim_time': use_sim_time
    #     }.items()
    # )

    controllers = ["joint_state_broadcaster", "arm_controller", "gripper_controller"]
    delays = [20.0, 30.0, 40.0]

    for controller, delay in zip(controllers, delays):
        ld.add_action(
            TimerAction(
                period=delay,
                actions=[
                    Node(
                        package="controller_manager",
                        executable="spawner",
                        arguments=[
                            controller,
                            "--controller-manager",
                            "/controller_manager",
                            "--controller-manager-timeout",
                            "60.0",
                            "--switch-timeout",
                            "60.0",
                            "--service-call-timeout",
                            "60.0",
                        ],
                        parameters=[{'use_sim_time': True}],
                        output='screen'
                    )
                ]
            )
        )

    # ld.add_action(load_controllers_cmd)
    # Start Gazebo
    start_gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments=[('gz_args', ['-r -v 4 --physics-engine gz-physics-bullet-featherstone-plugin ', world_path]), ('use_sim_time', 'true')],
        condition=IfCondition(LaunchConfiguration("use_gazebo_gui")),
    )

    start_gazebo_headless_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments=[('gz_args', ['-s -r -v 4 --physics-engine gz-physics-bullet-featherstone-plugin ', world_path]), ('use_sim_time', 'true')],
        condition=UnlessCondition(LaunchConfiguration("use_gazebo_gui")),
    )


    # Start Gazebo ROS Bridge
    # Ignition sensor topics use the full world/model/link path
    _gz_cam = '/world/default/model/ur/link/base_link/sensor/camera_head'
    start_gazebo_ros_image_bridge_cmd = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=[
            f'{_gz_cam}/depth_image',
            f'{_gz_cam}/image',
        ],
        remappings=[
            (f'{_gz_cam}/depth_image', '/camera_head/depth/image_rect_raw'),
            (f'{_gz_cam}/image',       '/camera_head/color/image_raw'),
        ],
    )


    # Spawn robot in Gazebo
    start_gazebo_ros_spawner_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', '/robot_description',
            '-name', robot_name,
            '-allow_renaming', 'true',
            '-x', '0.0',  
            '-y', '0.0',  
            '-z', '0.0',   # Optional: Set Z position to 0.0 (you can adjust based on your need)
            '-R', '0.0',   # Optional: Set Roll rotation to 0.0 (adjust as needed)
            '-P', '0.0',   # Optional: Set Pitch rotation to 0.0 (adjust as needed)
            '-Y', '0.0'    # Optional: Set Yaw rotation to 0.0 (adjust as needed)
        ]
    )

    robotiq_condition = IfCondition(
        PythonExpression([
            "'",
            gripper,
            "' in ['robotiq_2f_85', 'robotiq_2f_140'] and '",
            LaunchConfiguration("use_rviz"),
            "' == 'true'",
        ])
    )
    onrobot_condition = IfCondition(
        PythonExpression([
            "'",
            gripper,
            "' in ['onrobot_rg2', 'onrobot_rg6'] and '",
            LaunchConfiguration("use_rviz"),
            "' == 'true'",
        ])
    )

    robotiq_move_group_condition = IfCondition(
        PythonExpression([
            "'",
            gripper,
            "' in ['robotiq_2f_85', 'robotiq_2f_140'] and '",
            LaunchConfiguration("use_move_group"),
            "' == 'true'",
        ])
    )
    onrobot_move_group_condition = IfCondition(
        PythonExpression([
            "'",
            gripper,
            "' in ['onrobot_rg2', 'onrobot_rg6'] and '",
            LaunchConfiguration("use_move_group"),
            "' == 'true'",
        ])
    )

    rviz_node_robotiq = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
        parameters=[
            robot_description,
            moveit_config_robotiq.robot_description_semantic,
            moveit_config_robotiq.robot_description_kinematics,
            moveit_config_robotiq.planning_pipelines,
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
            robot_description,
            moveit_config_onrobot.robot_description_semantic,
            moveit_config_onrobot.robot_description_kinematics,
            moveit_config_onrobot.planning_pipelines,
            {"use_sim_time": use_sim_time}
        ],
        condition=onrobot_condition,
    )

    move_group_parameters_robotiq = moveit_config_robotiq.to_dict()
    move_group_parameters_robotiq.update(robot_description)
    move_group_parameters_onrobot = moveit_config_onrobot.to_dict()
    move_group_parameters_onrobot.update(robot_description)

    # ExecuteTaskSolutionCapability is required for MTC pick-and-place execution
    mtc_capabilities = {"capabilities": "move_group/ExecuteTaskSolutionCapability"}

    move_group_node_robotiq = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[move_group_parameters_robotiq, {"use_sim_time": use_sim_time}, mtc_capabilities],
        condition=robotiq_move_group_condition,
    )

    move_group_node_onrobot = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[move_group_parameters_onrobot, {"use_sim_time": use_sim_time}, mtc_capabilities],
        condition=onrobot_move_group_condition,
    )

    ld.add_action(set_env_vars_resources)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(start_gazebo_cmd)
    ld.add_action(start_gazebo_headless_cmd)
    ld.add_action(start_gazebo_ros_bridge_cmd)
    ld.add_action(start_gazebo_ros_image_bridge_cmd)
    ld.add_action(start_gazebo_ros_spawner_cmd)
    ld.add_action(move_group_node_robotiq)
    ld.add_action(move_group_node_onrobot)
    ld.add_action(rviz_node_robotiq)
    ld.add_action(rviz_node_onrobot)

    return ld
