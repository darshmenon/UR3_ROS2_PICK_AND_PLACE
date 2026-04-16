
# UR Robotic Arm with Robotiq 2-Finger Gripper for ROS 2

Related Blog Post: For behind-the-scenes details and the full development journey, check out the companion Medium article:
[How I'm Building an Autonomous Pick-and-Place System with ROS 2 Jazzy and Gazebo Harmonic](https://medium.com/@darshmenon02/how-i-am-building-an-autonomous-pick-and-place-system-with-ros-2-jazzy-and-gazebo-harmonic-6474cbcc8dc7)

The blog dives into simulation setup, robotic control, MoveIt Task Constructor, and lessons learned — perfect if you're curious about the engineering side or want to replicate the project from scratch.

This project integrates the Robotiq 2-Finger Gripper with a Universal Robots UR3 arm using **ROS 2 Humble / Jazzy** and **Ignition Gazebo**. It includes URDF models, ROS 2 control configuration, simulation launch files, MoveIt Task Constructor pick-and-place, vision-based object detection, LLM-driven task planning (Ollama), and demonstration recording for behavior cloning.

> **Note:** This setup uses **fixed mimic joint configuration** for the Robotiq gripper to support simulation in newer Gazebo (Harmonic). Only the primary `finger_joint` receives commands — mimic joints automatically follow.

---

## Demo

![alt text](assets/exec.gif)

![alt text](<assets/gazebo_simonline-video-cutter.com-ezgif.com-video-to-gif-converter (1).gif>)

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
# Set to humble or jazzy
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

> **Jazzy only** — add these two extra packages:
> ```bash
> sudo apt install ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge \
>                  ros-jazzy-moveit-planners-stomp
> ```
> STOMP is not packaged for Humble so leave it out there — the planner init fails silently and is harmless.

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

### MongoDB (required for warehouse_ros_mongo)

MTC uses `warehouse_ros_mongo` to persist planning scenes and trajectories. MongoDB must be installed and running before launching the demo:

```bash
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | \
  sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \
  sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

sudo apt-get update && sudo apt-get install -y mongodb-org
sudo systemctl start mongod && sudo systemctl enable mongod
```

Verify it is running: `mongosh` should connect to `mongodb://127.0.0.1:27017`.

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

![Arm with Gripper](/assets/arm_with_gripper.png)

### Robotiq Gripper Close-up

![Gripper](/assets/gripper.png)

### Simulation in Gazebo

![Gazebo View](/assets/image.png)

### RViz Overview

![RViz 1](/assets/rviz1.png)

### MTC Overview

![MTC](/assets/mtc.png)

### Pick Error

![pick error](assets/pick_error.png)

### MTC Pipeline

![MTC Pipeline](assets/mtc_pp.png)

### Loop Demo

![loop](assets/looponline-video-cutter.com-ezgif.com-video-to-gif-converter.gif)

### Colour Pick

![colour pick](assets/colour_pick.png)

---

## AI / ML Stack

### Vision-Based Perception (`ur_perception`)

Color-based detection with optional YOLO and PCL cluster extraction from the Intel D435 camera.

```bash
ros2 launch ur_perception perception.launch.py
ros2 topic echo /detected_objects
```

Annotated image output: `/detection_image`

### SAC RL Policy Runner (`mujoco_ur_rl_ros2`)

Run a Soft Actor-Critic policy trained in MuJoCo on the simulated UR3.

Main node:

- `shared_arm_policy_node`: pick-and-place policy with arm + gripper

Run the policy in Gazebo:

```bash
# Terminal 1 — start simulation
ros2 launch ur_gazebo ur.gazebo.launch.py

# Terminal 2 — run shared-arm SAC policy
ros2 run mujoco_ur_rl_ros2 shared_arm_policy_node \
  --ros-args \
  -p model_path:=/path/to/best_model.zip \
  -p object_x:=0.45 -p object_y:=0.0 -p object_z:=0.045 \
  -p drop_x:=0.45  -p drop_y:=0.2  -p drop_z:=0.025
```

Or launch Gazebo and the policy together:

```bash
ros2 launch mujoco_ur_rl_ros2 gazebo_shared_arm_policy.launch.py \
  model_path:=/path/to/best_model.zip \
  launch_policy:=true
```

The policy reads `/joint_states` and publishes to `/arm_controller/joint_trajectory` and `/gripper_controller/joint_trajectory`.

Train a Gazebo-aligned policy:

```bash
python3 mujoco_ur_rl_ros2/train_gazebo_single_arm.py \
  --timesteps 2000000 \
  --n-envs 8 \
  --curriculum grasp_focus
```

Resume training:

```bash
python3 mujoco_ur_rl_ros2/train_gazebo_single_arm.py \
  --timesteps 2000000 \
  --n-envs 8 \
  --curriculum grasp_focus \
  --resume models/gazebo_single_arm/<run>/best_model.zip
```

Best checkpoint:

- `models/gazebo_single_arm/<run>/best_model.zip`

Key notes:

- `--curriculum grasp_focus` is the most important setting for grasp learning
- checkpoints are saved every `100k` steps
- `ur_gazebo_single_arm_env.py` is the main transfer env for Gazebo
- keep spawned objects inside the UR3 reachable workspace for better transfer

### Full Demo (all-in-one)

```bash
ros2 launch ur_gazebo full_demo.launch.py
ros2 launch ur_gazebo full_demo.launch.py use_llm_planner:=true
```

---

## Contributing

Feel free to open pull requests or issues for improvements or bug reports.

---

## How To View Training And Gazebo

### View Training Live (MuJoCo)

`train_gazebo_single_arm.py` trains in MuJoCo, not in Gazebo. To watch training live:

```bash
python3 mujoco_ur_rl_ros2/train_gazebo_single_arm.py \
  --timesteps 2000000 \
  --n-envs 1 \
  --curriculum grasp_focus \
  --render \
  --resume models/gazebo_single_arm/gazebo_single_arm_20260415_1430/best_model.zip
```

Use `--render` only with `--n-envs 1`.

### Run Training Headless

For faster training without the MuJoCo viewer:

```bash
python3 mujoco_ur_rl_ros2/train_gazebo_single_arm.py \
  --timesteps 2000000 \
  --n-envs 8 \
  --curriculum grasp_focus \
  --resume models/gazebo_single_arm/gazebo_single_arm_20260415_1430/best_model.zip
```

### View The Best Policy In Gazebo

Launch Gazebo and the saved policy together:

```bash
ros2 launch mujoco_ur_rl_ros2 gazebo_shared_arm_policy.launch.py \
  model_path:=/home/asimov/UR3_ROS2_PICK_AND_PLACE/models/gazebo_single_arm/gazebo_single_arm_20260415_1430/best_model.zip \
  launch_policy:=true
```

Important:

- Use `launch_policy:=true` if you want the RL policy node to start automatically.
- After launch, wait about `55` seconds before expecting arm motion.
- That delay is intentional so Gazebo, `gz_ros2_control`, and the arm/gripper controllers have time to come up cleanly before the policy starts sending commands.

Or run Gazebo and the policy separately:

```bash
ros2 launch ur_gazebo ur.gazebo.launch.py
```

```bash
ros2 run mujoco_ur_rl_ros2 shared_arm_policy_node \
  --ros-args \
  -p model_path:=/home/asimov/UR3_ROS2_PICK_AND_PLACE/models/gazebo_single_arm/gazebo_single_arm_20260415_1430/best_model.zip \
  -p arm_trajectory_topic:=/arm_controller/joint_trajectory \
  -p gripper_trajectory_topic:=/gripper_controller/joint_trajectory \
  -p object_x:=0.35 -p object_y:=0.0 -p object_z:=0.045 \
  -p drop_x:=0.35 -p drop_y:=0.20 -p drop_z:=0.025
```

The bundled Gazebo workflow uses `single_arm_transfer.world`, which is aligned with the single-arm MuJoCo training scene.

### Launch Both Together

Launch Gazebo and MuJoCo training from one command:

```bash
ros2 launch mujoco_ur_rl_ros2 dual_view_single_arm.launch.py
```

Useful variants:

```bash
# Gazebo + live MuJoCo training viewer
ros2 launch mujoco_ur_rl_ros2 dual_view_single_arm.launch.py \
  launch_training:=true \
  training_render:=true
```

```bash
# Training only
ros2 launch mujoco_ur_rl_ros2 dual_view_single_arm.launch.py \
  launch_gazebo:=false \
  launch_training:=true \
  training_render:=true
```

```bash
# Gazebo only with a specific checkpoint
ros2 launch mujoco_ur_rl_ros2 dual_view_single_arm.launch.py \
  launch_training:=false \
  model_path:=/absolute/path/to/best_model.zip
```

### Quick Summary

- MuJoCo viewer shows the live RL training environment.
- Headless mode runs the same trainer without opening the viewer.
- Gazebo shows the trained or best saved policy running on the ROS 2 simulation stack.
- `train_gazebo_single_arm.py` is named for Gazebo transfer, but the RL loop itself runs in MuJoCo.

---

## Future Scope

- Add a vision-language-action pipeline for task-conditioned robot control.
- Bring back LLM task planning as a stable feature for high-level commands such as pick, place, sort, and multi-step tabletop tasks.
- Connect perception, RL, and language planning more tightly so detected objects can be selected and manipulated from natural-language instructions.
- Improve MuJoCo-to-Gazebo transfer so learned grasping policies behave more consistently on the UR3 with the Robotiq gripper.
