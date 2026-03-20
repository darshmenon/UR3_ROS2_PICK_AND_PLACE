#!/usr/bin/env python3
"""
Launch file for the ur_llm_planner LLMPlannerNode.

Usage:
    ros2 launch ur_llm_planner llm_planner.launch.py
    ros2 launch ur_llm_planner llm_planner.launch.py auto_demo:=true
    ros2 launch ur_llm_planner llm_planner.launch.py ollama_model:=mistral:7b
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution


def generate_launch_description():
    config_file = PathJoinSubstitution(
        [FindPackageShare("ur_llm_planner"), "config", "planner_params.yaml"]
    )

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
    ollama_model_arg = DeclareLaunchArgument(
        "ollama_model",
        default_value="llama3.2:3b",
        description="Ollama model tag to use for task planning (e.g. llama3.2:3b, mistral:7b).",
    )
    ollama_base_url_arg = DeclareLaunchArgument(
        "ollama_base_url",
        default_value="http://localhost:11434",
        description="Base URL of the local Ollama server.",
    )

    llm_planner_node = Node(
        package="ur_llm_planner",
        executable="llm_planner_node",
        name="llm_planner_node",
        output="screen",
        parameters=[
            config_file,
            {
                "ollama_model": LaunchConfiguration("ollama_model"),
                "ollama_base_url": LaunchConfiguration("ollama_base_url"),
                "auto_demo": LaunchConfiguration("auto_demo"),
                "auto_demo_command": LaunchConfiguration("auto_demo_command"),
            },
        ],
    )

    return LaunchDescription(
        [
            auto_demo_arg,
            auto_demo_command_arg,
            ollama_model_arg,
            ollama_base_url_arg,
            llm_planner_node,
        ]
    )
