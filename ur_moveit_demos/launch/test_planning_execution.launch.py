from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    def configure_setup(context):
        gripper = LaunchConfiguration("gripper")
        gripper_str = gripper.perform(context)
        controllers_file = (
            "config/moveit_controllers_onrobot.yaml"
            if gripper_str in ("onrobot_rg2", "onrobot_rg6")
            else "config/moveit_controllers.yaml"
        )

        moveit_config = (
            MoveItConfigsBuilder("ur", package_name="moveit_config")
            .robot_description(file_path="config/ur.urdf.xacro", mappings={"gripper": gripper})
            .robot_description_semantic(file_path="config/ur.srdf.xacro", mappings={"gripper": gripper})
            .trajectory_execution(file_path=controllers_file)
            .to_moveit_configs()
        )

        moveit_dict = moveit_config.to_dict()
        moveit_dict.update({"use_sim_time": True})

        return [
            Node(
                package="ur_moveit_demos",
                executable="test_planning_execution",
                output="screen",
                parameters=[moveit_dict],
            )
        ]

    return LaunchDescription([
        DeclareLaunchArgument(
            "gripper",
            default_value="robotiq_2f_85",
            description="Gripper to attach to the robot",
            choices=["robotiq_2f_85", "robotiq_2f_140", "onrobot_rg2", "onrobot_rg6"],
        ),
        OpaqueFunction(function=configure_setup),
    ])
