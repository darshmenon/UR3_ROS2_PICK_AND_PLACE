"""Start the dual-arm whole-body coordinator (the dual-arm simulation must already be running)."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("max_object_speed", default_value="0.05", description="object speed along its path (m/s)"),
        DeclareLaunchArgument("max_joint_speed", default_value="1.0", description="joint speed cap (rad/s)"),
        Node(package="ur_dual_coordination", executable="coordinator_node.py", name="dual_coordinator", output="screen",
             parameters=[{"max_object_speed": LaunchConfiguration("max_object_speed"),
                          "max_joint_speed": LaunchConfiguration("max_joint_speed"),
                          # wall clock on purpose: its timers must keep running even if the sim publishes no /clock
                          "use_sim_time": False}]),
    ])
