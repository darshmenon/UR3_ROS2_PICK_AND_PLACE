# ur_grasp — Grasp Detection for UR3 + Robotiq 2F-85

Grasp detection node that works with **ROS 2 Humble and Jazzy**.

## Grasp Algorithms Included

Two backends are available and auto-selected at startup:

| Backend | Source | Deps | Works out-of-box |
|---------|--------|------|-----------------|
| **simple_grasping** (primary) | [ros-planning/simple_grasping](https://github.com/mikeferguson/simple_grasping) | `ros-$ROS_DISTRO-simple-grasping` apt pkg | Only if apt pkg installed |
| **CylinderGraspDetector** (fallback) | Built into this repo (`ur_grasp/cylinder_grasp_detector.py`) | `numpy`, `sensor_msgs` only | Always available |

The node automatically falls back to the numpy backend if `simple_grasping` is not installed — **no configuration needed**.

### simple_grasping
- CPU-only, cylinder/box-aware
- Calls the `FindGraspableObjects` action server
- Returns full `moveit_msgs/Grasp[]` with pre/post trajectories
- Install: `sudo apt install ros-$ROS_DISTRO-simple-grasping`

### CylinderGraspDetector (built-in fallback)
- Pure numpy, zero extra dependencies
- Pipeline: HSV colour filter → Z passthrough → centroid → grasp pose
- Grasp height: `min_z + 0.30 * object_height` (30% from bottom — optimal for Robotiq 2F-85 on cylinders)
- Works on any machine without any apt installs

## Installation

```bash
# From the UR3_ROS2_PICK_AND_PLACE workspace root:
colcon build --symlink-install --packages-select ur_grasp
source install/setup.bash

# Optional: install simple_grasping for the primary backend
sudo apt install ros-$ROS_DISTRO-simple-grasping
```

## Usage

```bash
# Start the grasp node (auto-selects backend)
ros2 run ur_grasp grasp_node

# Trigger detection
ros2 service call /ur_grasp/detect std_srvs/srv/Trigger {}

# Set colour filter before detecting
ros2 param set /grasp_node colour red   # red | blue | green | any
ros2 service call /ur_grasp/detect std_srvs/srv/Trigger {}
```

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/ur_grasp/grasp_pose` | `geometry_msgs/PoseStamped` | Best grasp pose in `base_link` frame |
| `/ur_grasp/grasp_marker` | `visualization_msgs/MarkerArray` | RViz visualization arrows |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `colour` | `"any"` | Colour filter: `red`, `blue`, `green`, `any` |
| `backend` | `"auto"` | Force backend: `simple_grasping`, `numpy`, or `auto` |
| `min_confidence` | `0.2` | Discard candidates below this confidence |

## Testing

```bash
python3 testing/test_grasp.py --colour red          # detect only
python3 testing/test_grasp.py --colour blue --execute  # detect + execute
```

## Portability

- Paths are fully dynamic — no hardcoded usernames or home directories
- Works on any machine with a valid ROS 2 workspace
- Compatible with ROS 2 **Humble** and **Jazzy**
