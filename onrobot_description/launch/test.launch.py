from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch_ros.substitutions import FindPackageShare

def lauch_setup(context):
    model = LaunchConfiguration('model')
    description_file = PathJoinSubstitution([FindPackageShare('onrobot_description'),'urdf','test.urdf.xacro'])
    rviz_config_file = PathJoinSubstitution([FindPackageShare('onrobot_description'),'rviz', 'urdf.rviz'])


    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            description_file,
            " ",
            "model:=",
            model,
            " ",
        ]
    )

    robot_description = {"robot_description": robot_description_content}

    # Robot state publisher
    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[robot_description],
    )
    # Joint state publisher
    joint_state_publisher = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher',
        output='screen',
    )
    # RVIZ
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz',
        output='screen',
        arguments=["-d", rviz_config_file],
    )
    return [
        node_robot_state_publisher,
        joint_state_publisher,
        rviz_node,
    ]

def generate_launch_description():
    declared_arguments = []
    declared_arguments.append(
        DeclareLaunchArgument(
            "model",
            default_value="rg2_v1",
            description="Model of the gripper to visualize in RVIZ (rg2_v1, rg6_v1, rg6_v2)"
        )
    )
    return LaunchDescription(declared_arguments + [OpaqueFunction(function=lauch_setup)])
