import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("ur", package_name="moveit_config")
        .robot_description(file_path="config/ur.urdf.xacro")
        .robot_description_semantic(file_path="config/ur.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .to_moveit_configs()
    )

    # Test Execution Node
    test_planning_execution_node = Node(
        package="ur_moveit_demos",
        executable="test_planning_execution",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": True}
        ],
    )

    return LaunchDescription([test_planning_execution_node])
