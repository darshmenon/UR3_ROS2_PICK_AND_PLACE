from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("camera_topic", default_value="/camera_wrist/depth/color/points"),
        DeclareLaunchArgument(
            "secondary_camera_topic",
            default_value="",
            description="Optional head camera cloud to fuse alongside wrist",
        ),
        DeclareLaunchArgument("colour", default_value="red"),
        DeclareLaunchArgument("remove_table", default_value="true"),
        DeclareLaunchArgument("outlier_filter", default_value="true"),
        DeclareLaunchArgument("save_path", default_value="/tmp/object.ply"),
        DeclareLaunchArgument("export_mesh", default_value="false"),
        DeclareLaunchArgument("save_metadata", default_value="true"),
        DeclareLaunchArgument("voxel_size", default_value="0.005"),
        DeclareLaunchArgument("roi_radius", default_value="0.20"),
        DeclareLaunchArgument("dwell_sec", default_value="1.5"),
        DeclareLaunchArgument("seg_sec", default_value="3.0"),
        DeclareLaunchArgument("max_views", default_value="5"),
        DeclareLaunchArgument("occlusion_aware", default_value="true"),
        DeclareLaunchArgument("use_sim_time", default_value="true",
                              description="Use the Gazebo /clock so TF stamp ages line up "
                                          "with the camera's simulated header stamps"),

        Node(
            package="ur_perception",
            executable="object_reconstructor_node.py",
            name="object_reconstructor_node",
            output="screen",
            parameters=[{
                "use_sim_time": ParameterValue(
                    LaunchConfiguration("use_sim_time"), value_type=bool
                ),
                "camera_topic": LaunchConfiguration("camera_topic"),
                "secondary_camera_topic": LaunchConfiguration("secondary_camera_topic"),
                "colour": LaunchConfiguration("colour"),
                "remove_table": ParameterValue(
                    LaunchConfiguration("remove_table"), value_type=bool
                ),
                "outlier_filter": ParameterValue(
                    LaunchConfiguration("outlier_filter"), value_type=bool
                ),
                "save_path": LaunchConfiguration("save_path"),
                "export_mesh": ParameterValue(
                    LaunchConfiguration("export_mesh"), value_type=bool
                ),
                "save_metadata": ParameterValue(
                    LaunchConfiguration("save_metadata"), value_type=bool
                ),
                "voxel_size": ParameterValue(
                    LaunchConfiguration("voxel_size"), value_type=float
                ),
                "roi_radius": ParameterValue(
                    LaunchConfiguration("roi_radius"), value_type=float
                ),
            }],
        ),
        Node(
            package="ur_perception",
            executable="reconstruct_sweep_node.py",
            name="reconstruct_sweep_node",
            output="screen",
            parameters=[{
                "dwell_sec": ParameterValue(
                    LaunchConfiguration("dwell_sec"), value_type=float
                ),
                "seg_sec": ParameterValue(
                    LaunchConfiguration("seg_sec"), value_type=float
                ),
                "max_views": ParameterValue(
                    LaunchConfiguration("max_views"), value_type=int
                ),
                "occlusion_aware": ParameterValue(
                    LaunchConfiguration("occlusion_aware"), value_type=bool
                ),
                "auto_start": True,
            }],
        ),
    ])
