from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("colour",  default_value="any",
                              description="Colour filter: red|blue|green|yellow|any"),
        DeclareLaunchArgument("backend", default_value="auto",
                              description="Backend: auto|simple_grasping|numpy"),

        Node(
            package="ur_grasp",
            executable="grasp_node",
            name="grasp_node",
            output="screen",
            parameters=[{
                "colour":  LaunchConfiguration("colour"),
                "backend": LaunchConfiguration("backend"),
            }],
        ),
    ])
