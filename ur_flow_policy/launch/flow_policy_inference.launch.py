from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'checkpoint',
            description='Path to a .pt checkpoint saved by train_flow_policy.py',
        ),
        DeclareLaunchArgument(
            'camera_topic',
            default_value='/camera_head/color/image_raw',
            description='RGB image topic from Gazebo camera',
        ),
        DeclareLaunchArgument(
            'control_hz',
            default_value='10.0',
            description='Control-loop rate in Hz',
        ),
        DeclareLaunchArgument(
            'action_scale',
            default_value='1.0',
            description='Scale applied to the predicted joint targets',
        ),
        DeclareLaunchArgument(
            'chunk_size',
            default_value='16',
            description='Action-chunk length (must match training)',
        ),
        DeclareLaunchArgument(
            'ode_steps',
            default_value='10',
            description='Euler steps used to integrate the flow-matching ODE',
        ),
        DeclareLaunchArgument(
            'temporal_ensemble_m',
            default_value='0.1',
            description='Decay rate for blending overlapping chunk predictions (0 disables)',
        ),
        DeclareLaunchArgument(
            'dinov2_backbone',
            default_value='facebook/dinov2-base',
            description='DINOv2 backbone id (must match the checkpoint)',
        ),
        Node(
            package='ur_flow_policy',
            executable='inference_node.py',
            name='flow_policy_inference',
            output='screen',
            parameters=[{
                'checkpoint':           LaunchConfiguration('checkpoint'),
                'camera_topic':         LaunchConfiguration('camera_topic'),
                'control_hz':           LaunchConfiguration('control_hz'),
                'action_scale':         LaunchConfiguration('action_scale'),
                'chunk_size':           LaunchConfiguration('chunk_size'),
                'ode_steps':            LaunchConfiguration('ode_steps'),
                'temporal_ensemble_m':  LaunchConfiguration('temporal_ensemble_m'),
                'dinov2_backbone':      LaunchConfiguration('dinov2_backbone'),
                'use_sim_time':         True,
            }],
        ),
    ])
