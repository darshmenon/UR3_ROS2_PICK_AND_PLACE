# Installation

Tested on Ubuntu 22.04 LTS with ROS 2 Humble.

---

## Using a different ROS 2 version

This project is developed and tested against ROS 2 Humble. If you are using a different version, follow these steps:

**Replace the distro name in every apt command.** For example, if using Iron or Jazzy, replace `humble` with your distro name everywhere in this guide:

```bash
# Humble
sudo apt install ros-humble-moveit

# Iron
sudo apt install ros-iron-moveit

# Jazzy
sudo apt install ros-jazzy-moveit
```

**Source the correct setup file** when building and running:

```bash
source /opt/ros/<your-distro>/setup.bash
```

**Check Gazebo compatibility.** Each ROS 2 version pairs with a specific Gazebo version:

| ROS 2 version | Recommended Gazebo | Bridge package        |
|---------------|--------------------|-----------------------|
| Humble        | Garden (gz-garden) | ros-humble-ros-gz     |
| Iron          | Fortress or Garden | ros-iron-ros-gz       |
| Jazzy         | Harmonic (gz-harmonic) | ros-jazzy-ros-gz  |

If you change the Gazebo version, update the `gz_args` in `ur_gazebo/launch/ur.gazebo.launch.py` and confirm the bridge topics match.

**MoveIt Task Constructor compatibility.** The `src/moveit_task_constructor` package in this repo targets Humble. For other distros, check if a compatible branch exists at https://github.com/moveit/moveit_task_constructor and replace the vendored source if needed.

**Not all packages are available on all distros via apt.** If a package is missing, check if it needs to be built from source and add it to `src/`.

---

## 1. ROS 2 Humble

Follow the official guide: https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html

Install the full desktop version:

```bash
sudo apt install ros-humble-desktop
```

Install colcon build tools:

```bash
sudo apt install python3-colcon-common-extensions python3-rosdep
```

---

## 2. Gazebo Garden

This project uses Gazebo Sim 7.x (Garden) with the ROS 2 Humble bridge.

```bash
sudo apt install gz-garden
sudo apt install ros-humble-ros-gz
sudo apt install ros-humble-ros-gz-bridge
sudo apt install ros-humble-ros-gz-image
sudo apt install ros-humble-ros-gz-sim
```

---

## 3. MoveIt 2

```bash
sudo apt install ros-humble-moveit
sudo apt install ros-humble-moveit-configs-utils
sudo apt install ros-humble-moveit-ros-move-group
sudo apt install ros-humble-moveit-ros-planning-interface
sudo apt install ros-humble-moveit-visual-tools
sudo apt install ros-humble-moveit-planners
sudo apt install ros-humble-moveit-planners-ompl
sudo apt install ros-humble-moveit-planners-chomp
sudo apt install ros-humble-pilz-industrial-motion-planner
sudo apt install ros-humble-stomp
sudo apt install ros-humble-moveit-simple-controller-manager
sudo apt install ros-humble-moveit-ros-warehouse
```

---

## 4. ros2_control and gz_ros2_control

```bash
sudo apt install ros-humble-ros2-control
sudo apt install ros-humble-ros2-controllers
sudo apt install ros-humble-gz-ros2-control
sudo apt install ros-humble-gz-ros2-control-demos
```

---

## 5. Point Cloud Library (PCL)

```bash
sudo apt install libpcl-dev
sudo apt install ros-humble-pcl-ros
sudo apt install ros-humble-pcl-conversions
```

---

## 6. MongoDB (required for warehouse_ros_mongo)

The `warehouse_ros_mongo` package (vendored in `src/`) requires a running MongoDB server.

Install the MongoDB server:

```bash
sudo apt install mongodb
```

Or install MongoDB Community Edition from the official source for more recent versions:
https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-ubuntu/

Install the C++ client library:

```bash
sudo apt install libmongoclient-dev
```

---

## 7. Additional ROS dependencies

```bash
sudo apt install ros-humble-generate-parameter-library
sudo apt install ros-humble-generate-parameter-library-py
sudo apt install ros-humble-warehouse-ros
sudo apt install ros-humble-xacro
sudo apt install ros-humble-joint-state-publisher
sudo apt install ros-humble-joint-state-publisher-gui
sudo apt install ros-humble-robot-state-publisher
sudo apt install ros-humble-rviz2
sudo apt install ros-humble-tf2-ros
sudo apt install ros-humble-tf2-eigen
sudo apt install ros-humble-tf2-geometry-msgs
```

---

## 8. Vendored packages (in src/)

These packages are included in the `src/` directory and are built from source with the workspace:

- `moveit_task_constructor` - MoveIt Task Constructor framework
- `warehouse_ros_mongo` - MongoDB backend for MoveIt warehouse

No separate installation is needed for these. They are built as part of the workspace.

---

## 9. Build the workspace

```bash
cd ~/UR3_ROS2_PICK_AND_PLACE
source /opt/ros/humble/setup.bash
rosdep install --from-paths . --ignore-src -r -y
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

> **Important:** Use `--symlink-install` so that config files (YAML, launch files) are symlinked into the install directory. This means edits to config files take effect immediately without a rebuild.

---

---

## 10. Kinematics solver

This project uses the **KDL kinematics plugin** (`kdl_kinematics_plugin/KDLKinematicsPlugin`) which is bundled with `ros-humble-moveit-kinematics` (installed via `ros-humble-moveit` above). No extra install is needed.

> **Note:** `trac_ik` is **not** used. Do not install `ros-humble-trac-ik-kinematics-plugin` — `kinematics.yaml` is already configured for KDL.

---

## 11. Run the pick and place demo

```bash
source install/setup.bash
bash ur_mtc_pick_place_demo/scripts/robot.sh
```

The script launches in this order:
1. Gazebo simulation with the UR robot and camera
2. MoveIt 2 move_group node and RViz
3. GetPlanningSceneServer (point cloud perception)
4. MTC pick and place node

---

## 12. Run the planning/execution test

To test that MoveIt planning and execution work correctly:

```bash
# Terminal 1 — launch the full simulation:
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py

# Wait ~45 seconds for Gazebo and all controllers to be active, then:

# Terminal 2 — run the test:
source install/setup.bash
ros2 launch ur_moveit_demos test_planning_execution.launch.py
```

---

## Troubleshooting

### `move_group` crashes immediately (exit code -6, SIGABRT)

Two known causes:

1. **Controller name mismatch** — `moveit_controllers.yaml` lists a controller in `controller_names` that has no config block. Every name in the list must have a matching config section.

2. **Missing kinematics plugin** — `kinematics.yaml` references a plugin that is not installed. This project uses `kdl_kinematics_plugin/KDLKinematicsPlugin`. Check `/opt/ros/humble/lib/libmoveit_kdl_kinematics_plugin.so` exists.

### `ros2_control_node` crashes immediately

This is **expected and harmless** in this Gazebo setup. Gazebo starts its own controller manager via the `gz_ros2_control` plugin. The standalone `ros2_control_node` in the launch file fails to load the `gz_ros2_control/GazeboSimSystem` hardware interface (which only works inside Gazebo) and exits. Controllers are still spawned by Gazebo's embedded manager.

### `MoveGroup action client/server not ready` / RViz spams "MoveGroup namespace changed"

Caused by `move_group` not running. Fix the SIGABRT causes above first.

### `No active joints or end effectors found for group 'arm'`

Symptom of `move_group` being down. Once move_group is running stably, RViz will pick up the robot model correctly.
