"""
Launch file for the ur_data_collector node.

Starts DataCollectorNode with parameters loaded from config/collector_params.yaml.
"""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg_share = FindPackageShare('ur_data_collector').find('ur_data_collector')
    default_params_file = os.path.join(pkg_share, 'config', 'collector_params.yaml')

    params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_params_file,
        description='Full path to the collector parameters YAML file.',
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock (Gazebo). Set to false for real hardware.',
    )

    collector_node = Node(
        package='ur_data_collector',
        executable='collector_node',
        name='data_collector_node',
        output='screen',
        parameters=[
            LaunchConfiguration('params_file'),
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
        ],
    )

    return LaunchDescription([
        params_file_arg,
        use_sim_time_arg,
        collector_node,
    ])
