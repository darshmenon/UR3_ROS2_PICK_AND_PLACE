from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'checkpoint',
            default_value='openvla/openvla-7b',
            description='HuggingFace repo ID or local path to OpenVLA checkpoint',
        ),
        DeclareLaunchArgument(
            'task',
            default_value='pick the red block and place it in the bin',
            description='Natural-language task description',
        ),
        DeclareLaunchArgument(
            'control_hz',
            default_value='10.0',
            description='Inference rate in Hz',
        ),
        DeclareLaunchArgument(
            'action_scale',
            default_value='0.05',
            description='Scale applied to predicted joint deltas',
        ),
        DeclareLaunchArgument(
            'camera_topic',
            default_value='/camera_head/color/image_raw',
            description='RGB image topic from Gazebo camera',
        ),
        Node(
            package='ur_smolvla',
            executable='inference_node.py',
            name='openvla_inference',
            output='screen',
            parameters=[{
                'checkpoint':    LaunchConfiguration('checkpoint'),
                'task':          LaunchConfiguration('task'),
                'control_hz':    LaunchConfiguration('control_hz'),
                'action_scale':  LaunchConfiguration('action_scale'),
                'camera_topic':  LaunchConfiguration('camera_topic'),
                'use_sim_time':  True,
            }],
        ),
    ])
