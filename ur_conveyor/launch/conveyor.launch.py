import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    ur_gazebo_share = get_package_share_directory("ur_gazebo")

    return LaunchDescription([
        DeclareLaunchArgument("spawn_interval_s", default_value="6.0"),
        DeclareLaunchArgument("belt_speed",       default_value="0.03"),

        # Launch Gazebo with the conveyor world. ur.gazebo.launch.py's
        # "world_file" argument is a bare filename joined internally against
        # its own worlds/ directory -- passing a full path here (as this file
        # previously did, under the wrong argument name "world") silently
        # loaded the default world instead.
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(ur_gazebo_share, "launch", "ur.gazebo.launch.py")
            ),
            # No mount table in this world: the default table_height (1.015) would leave the arm floating above the belt.
            launch_arguments={"world_file": "conveyor_sorting.world", "table_height": "0.0"}.items(),
        ),

        # Conveyor object spawner + mover
        Node(
            package="ur_conveyor",
            executable="conveyor_node",
            name="conveyor_node",
            output="screen",
            parameters=[{
                "spawn_interval_s": LaunchConfiguration("spawn_interval_s"),
                "belt_speed":       LaunchConfiguration("belt_speed"),
                "pick_zone_x":      0.35,
                "belt_y":           0.0,
                "belt_z":           0.075,
                "hold_timeout_s":   8.0,
                "world_name":       "default",
            }],
        ),
    ])
