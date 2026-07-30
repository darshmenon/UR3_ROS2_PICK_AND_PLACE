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
        DeclareLaunchArgument("camera_topic", default_value="/camera_wrist/depth/color/points",
                              description="Point cloud topic to detect from"),
        DeclareLaunchArgument("continuous_detect_hz", default_value="0.0",
                              description="If > 0, re-detect on a timer at this rate "
                                          "instead of only on /ur_grasp/detect calls"),

        Node(
            package="ur_grasp",
            executable="grasp_node",
            name="grasp_node",
            output="screen",
            parameters=[{
                "colour":  LaunchConfiguration("colour"),
                "backend": LaunchConfiguration("backend"),
                "camera_topic": LaunchConfiguration("camera_topic"),
                "continuous_detect_hz": LaunchConfiguration("continuous_detect_hz"),
            }],
        ),
    ])
