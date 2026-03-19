"""
Full demo launch file: Gazebo + MoveIt + optional perception and LLM planner.

Includes ur.gazebo.launch.py (full simulation stack), then optionally launches
the perception node and LLM planner after appropriate startup delays.

Usage:
    # Default (colored_blocks world, no LLM planner):
    ros2 launch ur_gazebo full_demo.launch.py

    # With LLM planner:
    ros2 launch ur_gazebo full_demo.launch.py use_llm_planner:=true

    # Custom world:
    ros2 launch ur_gazebo full_demo.launch.py world:=pick_and_place_demo.world
"""

import os
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # ------------------------------------------------------------------
    # Package share directories
    # ------------------------------------------------------------------
    pkg_ur_gazebo = FindPackageShare('ur_gazebo').find('ur_gazebo')

    # Optional packages (may not be installed yet)
    try:
        from launch_ros.substitutions import FindPackageShare as FPS
        pkg_ur_perception = FPS('ur_perception').find('ur_perception')
        perception_launch_path = os.path.join(
            pkg_ur_perception, 'launch', 'perception.launch.py'
        )
        perception_available = os.path.isfile(perception_launch_path)
    except Exception:
        perception_available = False
        perception_launch_path = None

    try:
        from launch_ros.substitutions import FindPackageShare as FPS
        pkg_ur_llm = FPS('ur_llm_planner').find('ur_llm_planner')
        llm_launch_path = os.path.join(
            pkg_ur_llm, 'launch', 'llm_planner.launch.py'
        )
        llm_available = os.path.isfile(llm_launch_path)
    except Exception:
        llm_available = False
        llm_launch_path = None

    # ------------------------------------------------------------------
    # Launch arguments
    # ------------------------------------------------------------------
    world_arg = DeclareLaunchArgument(
        'world',
        default_value='colored_blocks.world',
        description='Gazebo world file name (must exist in ur_gazebo/worlds/).',
    )

    use_llm_planner_arg = DeclareLaunchArgument(
        'use_llm_planner',
        default_value='false',
        description='Set to true to launch the LLM planner after startup.',
    )

    # Forward all ur.gazebo.launch.py arguments so they can be overridden
    robot_name_arg = DeclareLaunchArgument(
        'robot_name',
        default_value='ur',
        description='Name for the spawned robot.',
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock.',
    )

    ur_type_arg = DeclareLaunchArgument(
        'ur_type',
        default_value='ur3',
        description='UR robot type (ur3, ur5, etc.).',
    )

    # ------------------------------------------------------------------
    # Include ur.gazebo.launch.py (core simulation + MoveIt)
    # The 'world' argument maps to 'world_file' in ur.gazebo.launch.py
    # ------------------------------------------------------------------
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ur_gazebo, 'launch', 'ur.gazebo.launch.py')
        ),
        launch_arguments={
            'world_file': LaunchConfiguration('world'),
            'robot_name': LaunchConfiguration('robot_name'),
            'use_sim_time': LaunchConfiguration('use_sim_time'),
            'ur_type': LaunchConfiguration('ur_type'),
        }.items(),
    )

    # ------------------------------------------------------------------
    # Perception node (delayed 60s to let Gazebo + MoveIt fully start)
    # Only launched if the package is available
    # ------------------------------------------------------------------
    delayed_actions = []

    if perception_available:
        perception_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(perception_launch_path),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
        )
        delayed_perception = TimerAction(
            period=60.0,
            actions=[perception_launch],
        )
        delayed_actions.append(delayed_perception)
    else:
        # Emit a warning at launch time if perception package not found
        from launch.actions import LogInfo
        delayed_actions.append(
            TimerAction(
                period=60.0,
                actions=[
                    LogInfo(
                        msg=(
                            'ur_perception package not found. '
                            'Skipping perception node launch. '
                            'Build ur_perception and rebuild to enable.'
                        )
                    )
                ],
            )
        )

    # ------------------------------------------------------------------
    # LLM planner node (delayed 65s, only if use_llm_planner:=true)
    # ------------------------------------------------------------------
    if llm_available:
        llm_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(llm_launch_path),
            launch_arguments={
                'use_sim_time': LaunchConfiguration('use_sim_time'),
            }.items(),
            condition=IfCondition(LaunchConfiguration('use_llm_planner')),
        )
        delayed_llm = TimerAction(
            period=65.0,
            actions=[llm_launch],
        )
        delayed_actions.append(delayed_llm)
    else:
        from launch.actions import LogInfo
        from launch.conditions import IfCondition as IC
        delayed_actions.append(
            TimerAction(
                period=65.0,
                actions=[
                    LogInfo(
                        msg=(
                            'ur_llm_planner package not found. '
                            'Skipping LLM planner launch. '
                            'Build ur_llm_planner and rebuild to enable.'
                        ),
                        condition=IfCondition(LaunchConfiguration('use_llm_planner')),
                    )
                ],
            )
        )

    # ------------------------------------------------------------------
    # Assemble launch description
    # ------------------------------------------------------------------
    ld = LaunchDescription([
        world_arg,
        use_llm_planner_arg,
        robot_name_arg,
        use_sim_time_arg,
        ur_type_arg,
        gazebo_launch,
    ])

    for action in delayed_actions:
        ld.add_action(action)

    return ld
