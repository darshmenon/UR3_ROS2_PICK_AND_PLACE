from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("sim_time_timer", default_value="false",
                              description="Tick the control loop on /clock instead of the wall clock"),
        Node(
            package="ur_force_control",
            executable="joint_impedance_controller",
            name="joint_impedance_controller",
            output="screen",
            parameters=[{
                "joint_names": [
                    "shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
                    "wrist_1_joint", "wrist_2_joint", "wrist_3_joint",
                ],
                "stiffness": [80.0, 80.0, 60.0, 15.0, 15.0, 15.0],
                "damping": [8.0, 8.0, 6.0, 1.5, 1.5, 1.5],
                "effort_limits": [56.0, 56.0, 28.0, 12.0, 12.0, 12.0],
                "publish_rate_hz": 200.0,
                "debug_logging": False,
                "debug_log_period_ms": 200,
                "use_sim_time": True,
                "sim_time_timer": ParameterValue(LaunchConfiguration("sim_time_timer"), value_type=bool),
            }],
        ),
    ])
