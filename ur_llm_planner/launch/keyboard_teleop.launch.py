from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ur_llm_planner',
            executable='keyboard_teleop.py',
            name='keyboard_teleop',
            output='screen',
            prefix='xterm -e',
        ),
    ])
