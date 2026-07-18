from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="ur_force_control",
            executable="external_wrench_estimator",
            name="external_wrench_estimator",
            output="screen",
            parameters=[{
                "planning_group": "arm",
                "publish_rate_hz": 30.0,
                "force_threshold_n": 15.0,
                "use_sim_time": True,
            }],
        ),
    ])
