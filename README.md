
# UR Robotic Arm with Robotiq 2-Finger Gripper for ROS 2

Related Blog Post: For behind-the-scenes details and the full development journey, check out the companion Medium article:
[How I'm Building an Autonomous Pick-and-Place System with ROS 2 Jazzy and Gazebo Harmonic](https://medium.com/@darshmenon02/how-i-am-building-an-autonomous-pick-and-place-system-with-ros-2-jazzy-and-gazebo-harmonic-6474cbcc8dc7)

The blog dives into simulation setup, robotic control, MoveIt Task Constructor, and lessons learned — perfect if you're curious about the engineering side or want to replicate the project from scratch.

This project integrates the Robotiq 2-Finger Gripper with a Universal Robots UR3 arm using **ROS 2 Humble / Jazzy** and **Ignition Gazebo**. It includes URDF models, ROS 2 control configuration, simulation launch files, MoveIt Task Constructor pick-and-place, vision-based object detection, LLM-driven task planning (Ollama), and demonstration recording for behavior cloning.

> **Note:** This setup uses **fixed mimic joint configuration** for the Robotiq gripper to support simulation in newer Gazebo (Harmonic). Only the primary `finger_joint` receives commands — mimic joints automatically follow.

---

## Demo

![alt text](images/exec.gif)

![alt text](<images/gazebo_simonline-video-cutter.com-ezgif.com-video-to-gif-converter (1).gif>)

---

## Installation

Make sure you have [ROS 2 Humble](https://docs.ros.org/en/humble/index.html) or [ROS 2 Jazzy](https://docs.ros.org/en/jazzy/index.html) and Ignition Gazebo installed.

### 1. Clone the Repository

```bash
git clone https://github.com/darshmenon/UR3_ROS2_PICK_AND_PLACE.git
cd UR3_ROS2_PICK_AND_PLACE
```

### 2. Install ROS Dependencies

```bash
# Replace $ROS_DISTRO with humble or jazzy
export ROS_DISTRO=humble

sudo apt install ros-$ROS_DISTRO-rviz2 \
                 ros-$ROS_DISTRO-joint-state-publisher \
                 ros-$ROS_DISTRO-robot-state-publisher \
                 ros-$ROS_DISTRO-ros2-control \
                 ros-$ROS_DISTRO-ros2-controllers \
                 ros-$ROS_DISTRO-controller-manager \
                 ros-$ROS_DISTRO-joint-trajectory-controller \
                 ros-$ROS_DISTRO-position-controllers \
                 ros-$ROS_DISTRO-gz-ros2-control \
                 ros-$ROS_DISTRO-ros2controlcli \
                 ros-$ROS_DISTRO-moveit \
                 ros-$ROS_DISTRO-moveit-ros-perception \
                 ros-$ROS_DISTRO-simple-grasping \
                 ros-$ROS_DISTRO-cv-bridge \
                 ros-$ROS_DISTRO-tf2-ros \
                 ros-$ROS_DISTRO-tf2-geometry-msgs \
                 ros-$ROS_DISTRO-pcl-ros
```

### 3. Install Python Dependencies

```bash
pip3 install -r requirements.txt
# Ollama is required for the LLM planner:
# Install from https://ollama.com
# Then pull your preferred model:
ollama pull llama2:latest
```

### 4. Build the Workspace

```bash
colcon build --symlink-install
source install/setup.bash
```

---

## MoveIt Task Constructor Setup

This project supports [MoveIt Task Constructor (MTC)](https://github.com/ros-planning/moveit_task_constructor) for advanced pick-and-place planning.

**This repo already includes a patched MTC source** in `src/moveit_task_constructor/` that works for both **ROS 2 Humble and Jazzy** — no extra cloning needed. Just build normally:

```bash
colcon build --symlink-install
```

For Humble/Jazzy API differences and troubleshooting, see [`ur_mtc_pick_place_demo/README.md`](ur_mtc_pick_place_demo/README.md).

---

## Launch Instructions

### Full MTC Pick-and-Place Demo

```bash
bash ur_mtc_pick_place_demo/scripts/robot.sh
```

Launches Gazebo + MoveIt + planning scene server + MTC demo in sequence.

### Launch Full Simulation in Gazebo

```bash
ros2 launch ur_gazebo ur.gazebo.launch.py
```

### Launch Point Cloud Viewer (Gazebo + RViz)

```bash
bash ur_mtc_pick_place_demo/scripts/pointcloud.sh
```

### Launch RViz Visualization (UR3 + Gripper)

```bash
ros2 launch ur_description view_ur.launch.py ur_type:=ur3
```

### Launch Gripper Visualization Alone

```bash
ros2 launch robotiq_2finger_grippers robotiq_2f_85_gripper_visualization/launch/test_2f_85_model.launch.py
```

---

## Move the Arm from CLI

```bash
ros2 action send_goal /arm_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory \
'{
  "trajectory": {
    "joint_names": [
      "shoulder_pan_joint",
      "shoulder_lift_joint",
      "elbow_joint",
      "wrist_1_joint",
      "wrist_2_joint",
      "wrist_3_joint"
    ],
    "points": [
      {
        "positions": [0.0, -1.57, 1.57, 0.0, 1.57, 0.0],
        "time_from_start": { "sec": 2, "nanosec": 0 }
      }
    ]
  }
}'
```

---

## Run Arm-Gripper Automation Script

```bash
python3 ~/UR3_ROS2_PICK_AND_PLACE/ur_system_tests/scripts/arm_gripper_loop_controller.py
```

---

## Sequential Hierarchical Pick-and-Place

Picks cylinders using a 10-step plan: `INIT → PRE_GRASP → DESCEND → GRASP → LIFT → TRANSPORT → LOWER → RELEASE → RETREAT → RETURN`

```bash
source install/setup.bash
python3 testing/pick_cylinders.py           # both cylinders
python3 testing/pick_cylinders.py --blue
python3 testing/pick_cylinders.py --green
python3 testing/pick_cylinders.py --red
python3 testing/pick_cylinders.py --dry     # print plan only
```

---

## Grasp Detection (ur_grasp)

Estimates grasp poses from the Intel D435 point cloud. Two backends:

| Backend | Method | Dependency |
|---|---|---|
| simple_grasping (primary) | PCL RANSAC → `moveit_msgs/Grasp[]` | `ros-$ROS_DISTRO-simple-grasping` |
| numpy centroid (fallback) | Colour HSV filter + centroid + height | built-in |

```bash
ros2 launch ur_grasp grasp_detection.launch.py colour:=red
python3 testing/test_grasp.py --colour red --execute
```

---

## Standalone Robot Control GUI

```bash
source install/setup.bash
python3 ur_llm_planner/scripts/robot_gui.py
```

Features: live camera feed, preset poses, gripper control (Open/Half/Close), per-joint sliders, Pilz PTP execution.

---

## Custom Zig-Zag Motion Demo

```bash
ros2 run ur_moveit_demos custom_zigzag_motion
```

Wait at least 45 seconds after launching the simulation before running this.

---

## MTC Demo Script

### Make the Script Executable

```bash
chmod +x ~/UR3_ROS2_PICK_AND_PLACE/ur_mtc_pick_place_demo/scripts/robot.sh
```

### Run the Script

```bash
~/UR3_ROS2_PICK_AND_PLACE/ur_mtc_pick_place_demo/scripts/robot.sh
```

This script launches the Gazebo simulation, MoveIt 2, the planning scene server, and the MTC pick-and-place demo.

---

## Screenshots

### UR3 with Robotiq Gripper in RViz

![Arm with Gripper](/images/arm_with_gripper.png)

### Robotiq Gripper Close-up

![Gripper](/images/gripper.png)

### Simulation in Gazebo

![Gazebo View](/images/image.png)

### RViz Overview

![RViz 1](/images/rviz1.png)

### MTC Overview

![MTC](/images/mtc.png)

### Pick Error

![pick error](images/pick_error.png)

### MTC Pipeline

![MTC Pipeline](images/mtc_pp.png)

### Loop Demo

![loop](images/looponline-video-cutter.com-ezgif.com-video-to-gif-converter.gif)

### Colour Pick

![colour pick](colour_pick.png)

---

## AI / ML Stack

### Vision-Based Perception (`ur_perception`)

Color + optional YOLO object detection + PCL-based cluster extraction from the Intel D435 camera.

```bash
ros2 launch ur_perception perception.launch.py
ros2 topic echo /detected_objects
# Annotated feed in RViz: /detection_image
```

### LLM Task Planning (`ur_llm_planner`)

Natural language to robot motion via local Ollama model:

```bash
ros2 launch ur_llm_planner llm_planner.launch.py
ros2 topic pub --once /llm_planner/command std_msgs/msg/String \
  "{data: 'pick up the red block and place it in the left bin'}"
```

### Demonstration Recording + Behavior Cloning (`ur_data_collector`)

```bash
ros2 launch ur_data_collector data_collector.launch.py
ros2 service call /data_collector/start_recording std_srvs/srv/Trigger
ros2 service call /data_collector/stop_recording std_srvs/srv/Trigger

python3 ur_data_collector/scripts/train_bc.py \
  --data_dir ~/ur3_demos \
  --output_dir ~/bc_policy \
  --epochs 50
```

### SmolVLA Vision-Language-Action Policy (`ur_smolvla`)

[SmolVLA](https://huggingface.co/lerobot/smolvla_base) is a compact VLA model from HuggingFace that takes a camera image + joint states and predicts robot actions directly from a natural-language task description. This replaces hardcoded waypoints with a learned policy.

**Install lerobot (requires Python >= 3.11):**

```bash
python3.11 -m pip install "git+https://github.com/huggingface/lerobot.git#egg=lerobot[smolvla]"
```

**Run inference against the base model:**

```bash
# Terminal 1 — start simulation
ros2 launch ur_gazebo ur.gazebo.launch.py

# Terminal 2 — run SmolVLA inference
ros2 launch ur_smolvla smolvla_inference.launch.py \
  task:="pick the red block and place it in the bin"
```

**Run with a fine-tuned checkpoint:**

```bash
ros2 launch ur_smolvla smolvla_inference.launch.py \
  checkpoint:=/path/to/your/checkpoint \
  task:="pick the red block"
```

The inference node subscribes to `/camera_head/color/image_raw` + `/joint_states` and publishes `JointTrajectory` commands to `/arm_controller/joint_trajectory` at 10 Hz. The camera is a simulated Intel D435 mounted at 0.50 m height with a 25° downward tilt, giving a clear view of the workspace.

**Workflow to fine-tune SmolVLA on your own pick-and-place demos:**

1. Record demonstrations with `ur_data_collector` (saves HDF5 episodes)
2. Convert to LeRobot dataset format and fine-tune SmolVLA
3. Point `checkpoint:=` at your fine-tuned model and run inference

### Full Demo (all-in-one)

```bash
ros2 launch ur_gazebo full_demo.launch.py
ros2 launch ur_gazebo full_demo.launch.py use_llm_planner:=true
```

---

## Contributing

Feel free to open pull requests or issues for improvements or bug reports.
