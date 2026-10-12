import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # world_file is joined against ur_gazebo/worlds; an absolute path overrides the join.
    return LaunchDescription([
        DeclareLaunchArgument('world', description='absolute path to a splat2scene world.sdf'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution(
                [FindPackageShare('ur_gazebo'), 'launch', 'ur.gazebo.launch.py'])),
            launch_arguments={'world_file': LaunchConfiguration('world')}.items()),
    ])
