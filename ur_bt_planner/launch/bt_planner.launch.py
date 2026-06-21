from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("pick_x",  default_value="0.35"),
        DeclareLaunchArgument("pick_y",  default_value="0.0"),
        DeclareLaunchArgument("pick_z",  default_value="0.05"),
        DeclareLaunchArgument("place_x", default_value="0.15"),
        DeclareLaunchArgument("place_y", default_value="0.30"),
        DeclareLaunchArgument("place_z", default_value="0.08"),
        Node(
            package="ur_bt_planner",
            executable="bt_planner_node",
            name="bt_planner_node",
            output="screen",
            parameters=[{
                "pick_x":  LaunchConfiguration("pick_x"),
                "pick_y":  LaunchConfiguration("pick_y"),
                "pick_z":  LaunchConfiguration("pick_z"),
                "place_x": LaunchConfiguration("place_x"),
                "place_y": LaunchConfiguration("place_y"),
                "place_z": LaunchConfiguration("place_z"),
                "tick_rate_hz": 10.0,
                "use_compliant_grasp": True,
            }],
        ),
    ])
