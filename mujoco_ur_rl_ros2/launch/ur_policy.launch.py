from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "model_path",
                default_value="/home/asimov/mujoco-ur-arm-rl/models/best_model.zip",
            ),
            DeclareLaunchArgument("target_x", default_value="0.4"),
            DeclareLaunchArgument("target_y", default_value="0.0"),
            DeclareLaunchArgument("target_z", default_value="0.4"),
            DeclareLaunchArgument("joint_state_topic", default_value="/joint_states"),
            DeclareLaunchArgument(
                "trajectory_topic",
                default_value="/scaled_joint_trajectory_controller/joint_trajectory",
            ),
            DeclareLaunchArgument("control_rate_hz", default_value="10.0"),
            DeclareLaunchArgument("action_scale", default_value="0.5"),
            DeclareLaunchArgument("step_dt", default_value="0.1"),
            Node(
                package="mujoco_ur_rl_ros2",
                executable="ur_policy_node",
                name="ur_policy_node",
                output="screen",
                parameters=[
                    {
                        "model_path": LaunchConfiguration("model_path"),
                        "target_x": LaunchConfiguration("target_x"),
                        "target_y": LaunchConfiguration("target_y"),
                        "target_z": LaunchConfiguration("target_z"),
                        "joint_state_topic": LaunchConfiguration("joint_state_topic"),
                        "trajectory_topic": LaunchConfiguration("trajectory_topic"),
                        "control_rate_hz": LaunchConfiguration("control_rate_hz"),
                        "action_scale": LaunchConfiguration("action_scale"),
                        "step_dt": LaunchConfiguration("step_dt"),
                    }
                ],
            ),
        ]
    )
