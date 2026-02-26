# ur_gazebo

This package contains launch files and configurations for simulating the UR robot arm in Gazebo.

## Getting Started

To launch the robotic arm in Gazebo and RViz without MoveIt Task Constructor (MTC), you can run:

```bash
ros2 launch ur_gazebo ur.gazebo.launch.py
```

This launch file will:
1. Start the Gazebo simulation environment.
2. Spawn the UR arm.
3. Start the ROS 2 Control spawner for the arm and gripper controllers.
4. Launch RViz with the correct configuration.

Note: MTC packages can be ignored using COLCON_IGNORE to speed up build time if they are not needed.
