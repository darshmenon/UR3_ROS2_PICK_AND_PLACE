"""One command for the MoveIt Task Constructor pick and place: Gazebo + MoveIt, then MTC.

MTC needs two launch files (the simulator with move_group, then the MTC stack), and the second one fails
if it starts before move_group is up. This starts the first, waits, then starts the second.

    ros2 launch ur_gazebo mtc_demo.launch.py                       # default gripper (UR_GRIPPER, else onrobot_rg2)
    ros2 launch ur_gazebo mtc_demo.launch.py gripper:=robotiq_2f_85 max_attempts:=5
    ros2 service call /mtc_bt/run std_srvs/srv/Trigger {}          # start a pick and place (retries on failure)
    ros2 topic echo /mtc_bt/status
"""
import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare("ur_gazebo"), "/launch/ur.gazebo.launch.py"]),
        launch_arguments={
            "gripper": LaunchConfiguration("gripper"),
            "world_file": LaunchConfiguration("world_file"),
            "use_gazebo_gui": LaunchConfiguration("use_gazebo_gui"),
            "use_rviz": LaunchConfiguration("use_rviz"),
        }.items(),
    )
    mtc = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([FindPackageShare("ur_bt_planner"), "/launch/mtc_retry.launch.py"]),
        launch_arguments={
            "gripper": LaunchConfiguration("gripper"),
            "max_attempts": LaunchConfiguration("max_attempts"),
        }.items(),
    )
    return LaunchDescription([
        DeclareLaunchArgument("gripper", default_value=os.environ.get("UR_GRIPPER", "onrobot_rg2"),
                              description="robotiq_2f_85, robotiq_2f_140, onrobot_rg2 or onrobot_rg6"),
        DeclareLaunchArgument("world_file", default_value="colored_cylinder.world",
                              description="World with the object to pick (a bare filename from ur_gazebo/worlds)"),
        DeclareLaunchArgument("use_gazebo_gui", default_value="true"),
        DeclareLaunchArgument("use_rviz", default_value="true"),
        DeclareLaunchArgument("max_attempts", default_value="5", description="pick-place attempts before giving up"),
        DeclareLaunchArgument("mtc_delay", default_value="50.0", description="seconds to let Gazebo + move_group come up"),
        sim,
        LogInfo(msg="Gazebo + MoveIt starting; MTC follows after mtc_delay seconds"),
        TimerAction(period=LaunchConfiguration("mtc_delay"), actions=[LogInfo(msg="Starting MTC"), mtc]),
    ])
