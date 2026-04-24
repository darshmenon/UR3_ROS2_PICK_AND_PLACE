from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import FindExecutable, PathJoinSubstitution, Command, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from launch.conditions import IfCondition


def launch_setup(context):
  # Arguments
  use_sim_time = LaunchConfiguration('use_sim_time')
  launch_rviz = LaunchConfiguration('launch_rviz')
  model = LaunchConfiguration('model')

  # URDF file
  description_file = PathJoinSubstitution([FindPackageShare('onrobot_description'),'urdf','test.urdf.xacro'])
  # rviz 
  rviz_config_file = PathJoinSubstitution([FindPackageShare('onrobot_description'),'rviz', 'urdf.rviz'])

  world_file = PathJoinSubstitution([FindPackageShare('onrobot_description'),'world', 'test.sdf']).perform(context)
  print("World file: ", world_file)
  
  # Robot description
  robot_description_content = Command(
      [
          PathJoinSubstitution([FindExecutable(name='xacro')]),
          ' ',
          description_file,
          " ",
          "model:=",
          model,
          " ",
      ]
  )
  robot_description = {'robot_description':  ParameterValue(value=robot_description_content, value_type=str)}
  # Robot state publisher
  node_robot_state_publisher = Node(
    package='robot_state_publisher',
    executable='robot_state_publisher',
    output='both',
    parameters=[robot_description, {'use_sim_time': use_sim_time}],
  )
  # RViz
  rviz = Node(
      package="rviz2",
      executable="rviz2",
      name="rviz2",
      output="log",
      condition=IfCondition(launch_rviz),
      arguments=["-d", rviz_config_file],
  )
  # Gazebo
  # gazebo_launch = IncludeLaunchDescription( 
  #   PythonLaunchDescriptionSource([
  #     PathJoinSubstitution([FindPackageShare('ros_gz_sim'),
  #       'launch',
  #       'gz_sim.launch.py'])
  #   ]),
  #   # launch_arguments={'gz_args': '-r -v 4 empty.sdf --physics-engine gz-physics-bullet-featherstone-plugin'}.items()
  #   launch_arguments={'gz_args': ['-r -v 4', world_file]}.items(),
  # )
  gazebo_launch = IncludeLaunchDescription( 
    PythonLaunchDescriptionSource([
      PathJoinSubstitution([
        FindPackageShare('ros_gz_sim'),
        'launch',
        'gz_sim.launch.py',
      ])
    ]),
    launch_arguments={
        'gz_args': ['-r ', '-v 4 ', world_file] # Use the LaunchConfiguration
    }.items(),
  )

  # Spawn gripper in Gazebo
  spawn_gripper = Node(
    package='ros_gz_sim',
    executable='create',
    output='screen',
    arguments=['-topic', 'robot_description',
                '-name', model,
                '-allow_renaming', 'true'],
  )
  # Gazebo bridge
  gz_sim_bridge = Node(
      package="ros_gz_bridge",
      executable="parameter_bridge",
      arguments=[
          "/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock",
      ],
      output="screen",
  )
  # Controller launch
  
  controller_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
            FindPackageShare('onrobot_control'),
            'launch',
            'onrobot_rg_controller.launch.py',
            ])
        ]),
        launch_arguments={
            'prefix': [model, '_'],
            'controller_file': PathJoinSubstitution([FindPackageShare('onrobot_control'), 'config', 'onrobot_rg_standalone.yaml']),
            'standalone': "true"
        }.items()
    )

  
  return [
    node_robot_state_publisher, 
    rviz, 
    gazebo_launch, 
    spawn_gripper, 
    gz_sim_bridge, 
    controller_launch

  ]

def generate_launch_description():
  declared_arguments = []
  declared_arguments.append(DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulated clock'))
  declared_arguments.append(DeclareLaunchArgument('launch_rviz', default_value='true', description='Launch RViz'))
  declared_arguments.append(DeclareLaunchArgument('model', default_value='rg2_v1', description='Model name'))
  return LaunchDescription(declared_arguments + [OpaqueFunction(function=launch_setup)])
  