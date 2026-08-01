from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("colour",  default_value="any",
                              description="Colour filter: red|blue|green|yellow|any"),
        DeclareLaunchArgument("backend", default_value="auto",
                              description="Backend: auto|simple_grasping|numpy"),
        DeclareLaunchArgument("camera_topic", default_value="/camera_wrist/depth/color/points",
                              description="Point cloud topic to detect from"),
        DeclareLaunchArgument("use_reconstructed", default_value="false",
                              description="Prefer /ur_perception/reconstructed_points when available"),
        DeclareLaunchArgument("reconstructed_topic",
                              default_value="/ur_perception/reconstructed_points",
                              description="Fused multi-view cloud topic"),
        DeclareLaunchArgument("min_recon_points", default_value="200",
                              description="Ignore fused cloud below this many points"),
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
                "use_reconstructed": ParameterValue(
                    LaunchConfiguration("use_reconstructed"), value_type=bool
                ),
                "reconstructed_topic": LaunchConfiguration("reconstructed_topic"),
                "min_recon_points": ParameterValue(
                    LaunchConfiguration("min_recon_points"), value_type=int
                ),
                "continuous_detect_hz": ParameterValue(
                    LaunchConfiguration("continuous_detect_hz"), value_type=float
                ),
            }],
        ),
    ])
