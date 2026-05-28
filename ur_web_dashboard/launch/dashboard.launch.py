"""
Web dashboard launch.

Starts:
  - rosbridge_server WebSocket on port 9090
  - web_video_server MJPEG stream on port 8080

Then open:  file://<workspace>/ur_web_dashboard/web/index.html
  (or serve it:  python3 -m http.server 8000 --directory share/ur_web_dashboard/web)

Prerequisites:
    sudo apt install ros-humble-rosbridge-suite ros-humble-web-video-server
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("port",            default_value="9090"),
        DeclareLaunchArgument("video_port",      default_value="8080"),
        DeclareLaunchArgument("use_sim_time",    default_value="true"),

        Node(
            package="rosbridge_server",
            executable="rosbridge_websocket",
            name="rosbridge_websocket",
            output="screen",
            parameters=[{
                "port": LaunchConfiguration("port"),
                "use_sim_time": LaunchConfiguration("use_sim_time"),
            }],
        ),

        Node(
            package="web_video_server",
            executable="web_video_server",
            name="web_video_server",
            output="screen",
            parameters=[{
                "port": LaunchConfiguration("video_port"),
            }],
        ),
    ])
