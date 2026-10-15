"""
Native logging/plotting viewers, as an alternative to the web dashboard's
Logs card.

Starts:
  - rqt_console  : filterable table of /rosout messages
  - PlotJuggler   : live plots of numeric topics (joint states, effort, etc.)

Usage:
    ros2 launch ur_web_dashboard view_logs.launch.py
    ros2 launch ur_web_dashboard view_logs.launch.py plotjuggler:=false
    ros2 launch ur_web_dashboard view_logs.launch.py rqt_console:=false

Prerequisites:
    sudo apt install ros-humble-rqt-console ros-humble-plotjuggler-ros
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("rqt_console", default_value="true",
                               description="Launch rqt_console for /rosout"),
        DeclareLaunchArgument("plotjuggler", default_value="true",
                               description="Launch PlotJuggler for numeric topics"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),

        Node(
            package="rqt_console",
            executable="rqt_console",
            name="rqt_console",
            output="screen",
            condition=IfCondition(LaunchConfiguration("rqt_console")),
            parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
        ),

        Node(
            package="plotjuggler",
            executable="plotjuggler",
            name="plotjuggler",
            output="screen",
            condition=IfCondition(LaunchConfiguration("plotjuggler")),
            parameters=[{"use_sim_time": LaunchConfiguration("use_sim_time")}],
        ),
    ])
