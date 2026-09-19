"""
Launch Gazebo simulation with two independent UR robots (dual_ur.urdf.xacro).

Phase 2 of dual-arm support: spawns both arms in one Gazebo model, brings up
both controller sets, and now also move_group + RViz using dual_ur.srdf.xacro's
left_arm/right_arm/left_gripper/right_gripper groups (see dual_ur.srdf.xacro
and moveit_config/config/dual_*.yaml). Each arm can be planned/executed
independently through MoveIt/RViz — there is no bimanual (single-plan,
both-arms-together) MTC task graph yet, only the SRDF's "both_arms" group
declared for that future work (see README's Dual-Arm Support section).

Only robotiq_2f_85/robotiq_2f_140 grippers have SRDF groups today (dual_ur.srdf.xacro
doesn't cover onrobot_rg2/rg6 yet) — move_group/RViz are only started for those two.
See ur.gazebo.launch.py for the single-arm reference this was adapted from.
"""

import os
from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition, UnlessCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command, FindExecutable, PythonExpression
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    package_name_gazebo = 'ur_gazebo'
    package_name_moveit = 'moveit_config'

    default_world_file = 'colored_blocks.world'
    gazebo_models_path = 'models'
    gazebo_worlds_path = 'worlds'

    pkg_share_gazebo = FindPackageShare(package_name_gazebo).find(package_name_gazebo)
    moveit_config_share = FindPackageShare(package_name_moveit).find(package_name_moveit)
    pkg_ros_gz_sim = FindPackageShare('ros_gz_sim').find('ros_gz_sim')

    # Same fix as ur.gazebo.launch.py: force the Harmonic-built gz_ros2_control
    # ahead of the apt (Fortress-built) one on the plugin search path.
    local_gz_plugin_path = FindPackageShare('gz_ros2_control').find('gz_ros2_control')
    local_gz_plugin_lib = os.path.join(os.path.dirname(local_gz_plugin_path), '..', 'lib')

    gazebo_models_path = os.path.join(pkg_share_gazebo, gazebo_models_path)

    world_file = LaunchConfiguration('world_file')
    world_path = PathJoinSubstitution([pkg_share_gazebo, gazebo_worlds_path, world_file])
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')
    gripper = LaunchConfiguration('gripper')
    table_height = LaunchConfiguration('table_height')
    left_y = LaunchConfiguration('left_y')
    right_y = LaunchConfiguration('right_y')

    declared_arguments = [
        DeclareLaunchArgument("robot_name", default_value="dual_ur", description="The name for the combined dual-arm model"),
        DeclareLaunchArgument("use_sim_time", default_value="true", description="Use simulation (Gazebo) clock if true"),
        DeclareLaunchArgument("world_file", default_value=default_world_file, description="World file name"),
        DeclareLaunchArgument(
            "gripper",
            default_value="robotiq_2f_85",
            description="Gripper on both arms (phase 1: shared choice, not per-arm)",
            choices=["robotiq_2f_85", "robotiq_2f_140", "onrobot_rg2", "onrobot_rg6"],
        ),
        DeclareLaunchArgument("use_gazebo_gui", default_value="true", description="Launch Gazebo with the GUI client"),
        DeclareLaunchArgument(
            "table_height",
            default_value="1.015",
            description="Height (m) both arm bases are raised above the world origin.",
        ),
        DeclareLaunchArgument("left_y", default_value="0.45", description="Left arm base Y offset (m)"),
        DeclareLaunchArgument("right_y", default_value="-0.45", description="Right arm base Y offset (m)"),
        DeclareLaunchArgument("use_rviz", default_value="true", description="Launch RViz2 (robotiq grippers only)"),
        DeclareLaunchArgument("use_move_group", default_value="true", description="Launch move_group node (robotiq grippers only)"),
    ]

    ld = LaunchDescription(declared_arguments)

    ld.add_action(AppendEnvironmentVariable(
        'GZ_SIM_SYSTEM_PLUGIN_PATH',
        local_gz_plugin_lib,
        prepend=True,
    ))
    ld.add_action(AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', gazebo_models_path))

    urdf_xacro_path = os.path.join(moveit_config_share, "config", "dual_ur.urdf.xacro")

    robot_description_content = Command([
        PathJoinSubstitution([FindExecutable(name="xacro")]),
        " ",
        urdf_xacro_path,
        " ",
        "gripper:=", gripper,
        " ",
        "table_height:=", table_height,
        " ",
        "left_y:=", left_y,
        " ",
        "right_y:=", right_y,
    ])
    robot_description = {'robot_description': ParameterValue(robot_description_content, value_type=str)}

    robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='both',
        parameters=[robot_description, {'use_sim_time': use_sim_time}]
    )

    # MoveIt / RViz -- only wired up for robotiq_2f_85/2f_140, since
    # dual_ur.srdf.xacro doesn't have onrobot groups yet.
    robotiq_move_group_condition = IfCondition(
        PythonExpression([
            "'", gripper, "' in ['robotiq_2f_85', 'robotiq_2f_140'] and '",
            LaunchConfiguration("use_move_group"), "' == 'true'",
        ])
    )
    robotiq_rviz_condition = IfCondition(
        PythonExpression([
            "'", gripper, "' in ['robotiq_2f_85', 'robotiq_2f_140'] and '",
            LaunchConfiguration("use_rviz"), "' == 'true'",
        ])
    )

    moveit_config_dual = (
        MoveItConfigsBuilder("dual_ur", package_name=package_name_moveit)
        .trajectory_execution(file_path=os.path.join(moveit_config_share, "config", "dual_moveit_controllers.yaml"))
        .robot_description_semantic(
            file_path=os.path.join(moveit_config_share, "config", "dual_ur.srdf.xacro"),
            mappings={'gripper': gripper},
        )
        .joint_limits(file_path=os.path.join(moveit_config_share, "config", "dual_joint_limits.yaml"))
        .robot_description_kinematics(file_path=os.path.join(moveit_config_share, "config", "dual_kinematics.yaml"))
        .pilz_cartesian_limits(file_path=os.path.join(moveit_config_share, "config", "pilz_cartesian_limits.yaml"))
        .planning_pipelines(pipelines=["ompl", "pilz_industrial_motion_planner"], default_planning_pipeline="ompl")
        .planning_scene_monitor(
            publish_robot_description=True,
            publish_robot_description_semantic=True,
            publish_planning_scene=True,
        )
        .to_moveit_configs()
    )
    moveit_config_dual.robot_description = robot_description

    move_group_parameters_dual = moveit_config_dual.to_dict()
    move_group_parameters_dual.update(robot_description)

    move_group_node_cmd = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[move_group_parameters_dual, {'use_sim_time': use_sim_time}],
        condition=robotiq_move_group_condition,
    )

    rviz_config_path = os.path.join(moveit_config_share, "rviz", "dual_ur.rviz")
    rviz_node_cmd = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_path],
        parameters=[
            robot_description,
            moveit_config_dual.robot_description_semantic,
            moveit_config_dual.robot_description_kinematics,
            moveit_config_dual.planning_pipelines,
            {"use_sim_time": use_sim_time},
        ],
        condition=robotiq_rviz_condition,
    )

    start_gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments=[('gz_args', ['-r -v 4 --physics-engine gz-physics-bullet-featherstone-plugin ', world_path]), ('use_sim_time', 'true')],
        condition=IfCondition(LaunchConfiguration("use_gazebo_gui")),
    )
    start_gazebo_headless_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')),
        launch_arguments=[('gz_args', ['-s -r -v 4 --physics-engine gz-physics-bullet-featherstone-plugin ', world_path]), ('use_sim_time', 'true')],
        condition=UnlessCondition(LaunchConfiguration("use_gazebo_gui")),
    )

    start_gazebo_ros_spawner_cmd = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-topic', '/robot_description',
            '-name', robot_name,
            '-allow_renaming', 'true',
            '-x', '0.0', '-y', '0.0', '-z', '0.0',
            '-R', '0.0', '-P', '0.0', '-Y', '0.0',
        ]
    )

    # Same chained-spawner-with-retry pattern as ur.gazebo.launch.py: spawners
    # share one controller_manager service, launching them in parallel causes
    # "already loaded"/timed-out-switch errors, so chain strictly and retry on
    # a failed exit rather than silently dropping a controller.
    _CONTROLLER_CHAIN = [
        "joint_state_broadcaster",
        "left_arm_controller",
        "right_arm_controller",
        "left_gripper_controller",
        "right_gripper_controller",
    ]
    _SPAWNER_MAX_RETRIES = 3

    def _make_spawner(controller):
        return Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                controller,
                "--controller-manager", "/controller_manager",
                "--controller-manager-timeout", "60.0",
                "--switch-timeout", "60.0",
                "--service-call-timeout", "60.0",
            ],
            parameters=[{'use_sim_time': True}],
            output='screen',
        )

    def _spawn_step(context, index=0, retries_left=_SPAWNER_MAX_RETRIES):
        if index >= len(_CONTROLLER_CHAIN):
            return []
        controller = _CONTROLLER_CHAIN[index]
        spawner = _make_spawner(controller)

        def _on_exit(event, ctx):
            if event.returncode == 0:
                return _spawn_step(ctx, index + 1, _SPAWNER_MAX_RETRIES)
            if retries_left > 0:
                return [LogInfo(
                    msg=f"[dual_ur.gazebo] {controller} spawner failed (exit "
                        f"{event.returncode}) — retrying ({retries_left} left)"
                )] + _spawn_step(ctx, index, retries_left - 1)
            return [LogInfo(
                msg=f"[dual_ur.gazebo] ERROR: {controller} spawner failed after "
                    f"{_SPAWNER_MAX_RETRIES} retries."
            )]

        return [spawner, RegisterEventHandler(OnProcessExit(target_action=spawner, on_exit=_on_exit))]

    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(start_gazebo_cmd)
    ld.add_action(start_gazebo_headless_cmd)
    ld.add_action(start_gazebo_ros_spawner_cmd)
    ld.add_action(OpaqueFunction(function=_spawn_step))
    ld.add_action(move_group_node_cmd)
    ld.add_action(rviz_node_cmd)

    # mount_table only exists in Gazebo (world file) and isn't in the URDF, so
    # MoveIt/RViz have no idea it's there -- add it once as a static collision
    # object so it shows up in RViz and blocks planning through it. Box matches
    # ur_gazebo/models/mount_table/model.sdf's tabletop (1.5x0.8x0.03 @ z=1.0).
    # Timer delay gives move_group's planning_scene_monitor time to subscribe
    # to /planning_scene before this one-shot publish goes out.
    add_table_scene_cmd = TimerAction(
        period=8.0,
        actions=[ExecuteProcess(
            cmd=[
                "ros2", "topic", "pub", "--once", "/planning_scene",
                "moveit_msgs/msg/PlanningScene",
                "{is_diff: true, world: {collision_objects: [{header: {frame_id: 'world'}, "
                "id: 'mount_table', primitives: [{type: 1, dimensions: [1.5, 0.8, 0.03]}], "
                "primitive_poses: [{position: {x: 0.0, y: 0.0, z: 1.0}, orientation: {w: 1.0}}], "
                # CollisionObject.operation is a ROS `byte`, not a plain int --
                # ros2 topic pub's YAML parser rejects a bare integer here and
                # needs !!binary-encoded base64 (AA== is one zero byte, ADD=0).
                "operation: !!binary AA==}]}}",
            ],
            condition=robotiq_move_group_condition,
        )],
    )
    ld.add_action(add_table_scene_cmd)

    return ld
