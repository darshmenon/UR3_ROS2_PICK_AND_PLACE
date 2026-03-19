#!/usr/bin/env python3
"""
Launch file for the ur_llm_planner LLMPlannerNode.

The Anthropic API key is read from the ANTHROPIC_API_KEY environment variable
at launch time if not set in config/planner_params.yaml.

Usage:
    ros2 launch ur_llm_planner llm_planner.launch.py
    ros2 launch ur_llm_planner llm_planner.launch.py auto_demo:=true
    ANTHROPIC_API_KEY=sk-... ros2 launch ur_llm_planner llm_planner.launch.py
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    # Resolve config file path
    config_file = PathJoinSubstitution(
        [FindPackageShare("ur_llm_planner"), "config", "planner_params.yaml"]
    )

    # Pull the API key from the environment at launch time so users
    # don't have to hard-code it in the YAML file.
    api_key_from_env = os.environ.get("ANTHROPIC_API_KEY", "")

    # Launch arguments
    auto_demo_arg = DeclareLaunchArgument(
        "auto_demo",
        default_value="false",
        description="If true, automatically run auto_demo_command 5 seconds after startup.",
    )
    auto_demo_command_arg = DeclareLaunchArgument(
        "auto_demo_command",
        default_value="pick up the red object and place it to the left of the robot",
        description="Natural language command to execute in auto-demo mode.",
    )
    claude_model_arg = DeclareLaunchArgument(
        "claude_model",
        default_value="claude-opus-4-6",
        description="Claude model identifier to use for task planning.",
    )

    llm_planner_node = Node(
        package="ur_llm_planner",
        executable="llm_planner_node.py",
        name="llm_planner_node",
        output="screen",
        parameters=[
            config_file,
            {
                # Environment variable takes precedence over the YAML default ("")
                "anthropic_api_key": api_key_from_env,
                "auto_demo": LaunchConfiguration("auto_demo"),
                "auto_demo_command": LaunchConfiguration("auto_demo_command"),
                "claude_model": LaunchConfiguration("claude_model"),
            },
        ],
    )

    return LaunchDescription(
        [
            auto_demo_arg,
            auto_demo_command_arg,
            claude_model_arg,
            llm_planner_node,
        ]
    )
