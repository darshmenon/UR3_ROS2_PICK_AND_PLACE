from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("camera_topic", default_value="/camera_wrist/depth/color/points",
                              description="Point cloud topic to fuse frames from"),
        DeclareLaunchArgument("voxel_size", default_value="0.005",
                              description="Merge grid size in metres"),
        DeclareLaunchArgument("roi_radius", default_value="0.15",
                              description="Keep points within this many metres of roi_center "
                                          "(or of the last /ur_grasp/grasp_pose, if published)"),
        DeclareLaunchArgument("save_path", default_value="",
                              description="If set, write an ASCII PLY here on "
                                          "/ur_perception/reconstruct/stop"),

        Node(
            package="ur_perception",
            executable="object_reconstructor_node.py",
            name="object_reconstructor_node",
            output="screen",
            parameters=[{
                "camera_topic": LaunchConfiguration("camera_topic"),
                "voxel_size": LaunchConfiguration("voxel_size"),
                "roi_radius": LaunchConfiguration("roi_radius"),
                "save_path": LaunchConfiguration("save_path"),
            }],
        ),
    ])
