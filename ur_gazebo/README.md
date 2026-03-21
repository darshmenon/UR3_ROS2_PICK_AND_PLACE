# ur_gazebo

This package contains launch files and configurations for simulating the UR robot arm in Gazebo.

## Getting Started

To launch the robotic arm in Gazebo and RViz without MoveIt Task Constructor (MTC), you can run:

```bash
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py
```

This launch file will:
1. Start the Gazebo simulation environment
2. Spawn the UR3 arm with Robotiq 2F-85 gripper
3. Start the ROS 2 Control spawner for the arm and gripper controllers (~45s delay)
4. Launch RViz with the MoveIt motion planning panel
5. Start the ROS-Gazebo bridge (camera topics, clock, point cloud)

Note: MTC packages can be ignored using COLCON_IGNORE to speed up build time if not needed.

---

## Camera

An Intel RealSense D435 RGBD camera is mounted on a torso stand above the robot, tilted 55° downward to view the workspace.

Published ROS topics (via `ros_gz_image` bridge):

| Topic | Type | Description |
|---|---|---|
| `/camera_head/color/image_raw` | `sensor_msgs/Image` | Color stream (424×240, 10 Hz) |
| `/camera_head/depth/image_rect_raw` | `sensor_msgs/Image` | Depth stream |
| `/camera_head/depth/color/points` | `sensor_msgs/PointCloud2` | RGBD point cloud |
| `/camera_head/depth/camera_info` | `sensor_msgs/CameraInfo` | Camera intrinsics |

View the color feed:
```bash
ros2 run rqt_image_view rqt_image_view
# Select /camera_head/color/image_raw
```

Or add to RViz: **Add → By topic → /camera_head/color/image_raw → Image**

---

## Robot Control GUI

A standalone tkinter GUI with live camera feed and joint control:

```bash
source install/setup.bash
python3 ur_llm_planner/scripts/robot_gui.py
```

---

## Controller Timing

Controllers are spawned with delays to wait for Gazebo physics to stabilise:

| Controller | Delay |
|---|---|
| `joint_state_broadcaster` | 35 s |
| `arm_controller` | 40 s |
| `gripper_controller` | 45 s |

Wait for `"You can start planning now!"` in the logs before sending motion commands.
