from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'checkpoint',
            default_value='lerobot/smolvla_base',
            description='HuggingFace repo ID or local path to SmolVLA checkpoint',
        ),
        DeclareLaunchArgument(
            'task',
            default_value='pick the colored block and place it in the bin',
            description='Natural-language task description for the VLA',
        ),
        DeclareLaunchArgument(
            'inference_hz',
            default_value='10.0',
            description='Inference rate in Hz',
        ),
        Node(
            package='ur_smolvla',
            executable='inference_node.py',
            name='smolvla_inference',
            output='screen',
            parameters=[{
                'checkpoint': LaunchConfiguration('checkpoint'),
                'task': LaunchConfiguration('task'),
                'inference_hz': LaunchConfiguration('inference_hz'),
                'use_sim_time': True,
            }],
        ),
    ])
