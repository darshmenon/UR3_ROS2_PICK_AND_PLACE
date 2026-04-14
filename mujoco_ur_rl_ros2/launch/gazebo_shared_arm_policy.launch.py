from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    world_file = LaunchConfiguration("world_file")
    robot_name = LaunchConfiguration("robot_name")
    ur_type = LaunchConfiguration("ur_type")
    use_sim_time = LaunchConfiguration("use_sim_time")
    launch_policy = LaunchConfiguration("launch_policy")
    policy_delay = LaunchConfiguration("policy_delay")

    default_gazebo_launch = PathJoinSubstitution(
        [FindPackageShare("ur_gazebo"), "launch", "ur.gazebo.launch.py"]
    )
    gazebo_launch_path = LaunchConfiguration("gazebo_launch_path", default=default_gazebo_launch)

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_path),
        launch_arguments={
            "world_file": world_file,
            "robot_name": robot_name,
            "ur_type": ur_type,
            "use_sim_time": use_sim_time,
        }.items(),
    )

    policy_node = Node(
        package="mujoco_ur_rl_ros2",
        executable="shared_arm_policy_node",
        name="shared_arm_policy_node",
        output="screen",
        condition=IfCondition(launch_policy),
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "model_path": LaunchConfiguration("model_path"),
                "joint_state_topic": LaunchConfiguration("joint_state_topic"),
                "arm_trajectory_topic": LaunchConfiguration("arm_trajectory_topic"),
                "gripper_trajectory_topic": LaunchConfiguration("gripper_trajectory_topic"),
                "arm_joint_names": LaunchConfiguration("arm_joint_names"),
                "gripper_joint_names": LaunchConfiguration("gripper_joint_names"),
                "control_rate_hz": LaunchConfiguration("control_rate_hz"),
                "action_scale": LaunchConfiguration("action_scale"),
                "gripper_scale": LaunchConfiguration("gripper_scale"),
                "step_dt": LaunchConfiguration("step_dt"),
                "publish_gripper": LaunchConfiguration("publish_gripper"),
                "ee_x": LaunchConfiguration("ee_x"),
                "ee_y": LaunchConfiguration("ee_y"),
                "ee_z": LaunchConfiguration("ee_z"),
                "object_x": LaunchConfiguration("object_x"),
                "object_y": LaunchConfiguration("object_y"),
                "object_z": LaunchConfiguration("object_z"),
                "drop_x": LaunchConfiguration("drop_x"),
                "drop_y": LaunchConfiguration("drop_y"),
                "drop_z": LaunchConfiguration("drop_z"),
                "phase": LaunchConfiguration("phase"),
            }
        ],
    )

    delayed_policy = TimerAction(period=policy_delay, actions=[policy_node])

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "gazebo_launch_path",
                default_value=default_gazebo_launch,
                description="Path to the UR Gazebo launch file. Defaults to the bundled ur_gazebo package.",
            ),
            DeclareLaunchArgument("world_file", default_value="colored_blocks.world"),
            DeclareLaunchArgument("robot_name", default_value="ur"),
            DeclareLaunchArgument("ur_type", default_value="ur3"),
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument("launch_policy", default_value="true"),
            DeclareLaunchArgument(
                "policy_delay",
                default_value="55.0",
                description="Seconds to wait before starting policy node so Gazebo controllers can spawn.",
            ),
            DeclareLaunchArgument(
                "model_path",
                default_value="",
                description="Absolute path to the SAC model zip. Leave empty to use the node's built-in default.",
            ),
            DeclareLaunchArgument("joint_state_topic", default_value="/joint_states"),
            DeclareLaunchArgument(
                "arm_trajectory_topic",
                default_value="/scaled_joint_trajectory_controller/joint_trajectory",
            ),
            DeclareLaunchArgument("gripper_trajectory_topic", default_value="/gripper_controller/joint_trajectory"),
            DeclareLaunchArgument(
                "arm_joint_names",
                default_value="['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']",
            ),
            DeclareLaunchArgument("gripper_joint_names", default_value="['finger_joint']"),
            DeclareLaunchArgument("control_rate_hz", default_value="10.0"),
            DeclareLaunchArgument("action_scale", default_value="0.2"),
            DeclareLaunchArgument("gripper_scale", default_value="0.02"),
            DeclareLaunchArgument("step_dt", default_value="0.1"),
            DeclareLaunchArgument("publish_gripper", default_value="true"),
            DeclareLaunchArgument("ee_x", default_value="0.0"),
            DeclareLaunchArgument("ee_y", default_value="0.0"),
            DeclareLaunchArgument("ee_z", default_value="0.0"),
            DeclareLaunchArgument("object_x", default_value="-1.18"),
            DeclareLaunchArgument("object_y", default_value="0.0"),
            DeclareLaunchArgument("object_z", default_value="0.045"),
            DeclareLaunchArgument("drop_x", default_value="-1.25"),
            DeclareLaunchArgument("drop_y", default_value="0.0"),
            DeclareLaunchArgument("drop_z", default_value="0.02"),
            DeclareLaunchArgument("phase", default_value="0.0"),
            gazebo,
            delayed_policy,
        ]
    )
