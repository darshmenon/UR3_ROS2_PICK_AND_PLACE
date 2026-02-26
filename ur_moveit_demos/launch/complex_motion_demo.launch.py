from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("ur", package_name="moveit_config")
        .robot_description(file_path="config/ur.urdf.xacro")
        .robot_description_semantic(file_path="config/ur.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .to_moveit_configs()
    )

    moveit_dict = moveit_config.to_dict()
    moveit_dict.update({"use_sim_time": True})

    demo_node = Node(
        package="ur_moveit_demos",
        executable="complex_motion_demo",
        output="screen",
        parameters=[moveit_dict],
    )

    return LaunchDescription([demo_node])
