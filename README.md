
# UR Robotic Arm with Robotiq 2-Finger Gripper for ROS 2

📖 Related Blog Post: For behind-the-scenes details and the full development journey, check out the companion Medium article:
👉 👉 [*How I’m Building an Autonomous Pick-and-Place System with ROS 2 Jazzy and Gazebo Harmonic*](https://medium.com/@darshmenon02/how-i-am-building-an-autonomous-pick-and-place-system-with-ros-2-jazzy-and-gazebo-harmonic-6474cbcc8dc7) 

The blog dives into simulation setup, robotic control, MoveIt Task Constructor, and lessons learned—perfect if you're curious about the engineering side or want to replicate the project from scratch.


This project integrates the Robotiq 2-Finger Gripper with a Universal Robots UR3 arm using **ROS 2 Humble** and **Ignition Gazebo**. It includes URDF models, ROS 2 control configuration, simulation launch files, MoveIt Task Constructor pick-and-place, vision-based object detection, LLM-driven task planning (Claude API), and demonstration recording for behavior cloning.

> ✅ **Note:** This setup uses **fixed mimic joint configuration** for the Robotiq gripper to support simulation in **newer Gazebo (Harmonic)**. Only the primary `finger_joint` receives commands—mimic joints automatically follow.

---

## Demo 
![alt text](images/exec.gif)

![alt text](<images/gazebo_simonline-video-cutter.com-ezgif.com-video-to-gif-converter (1).gif>)

## 📦 Installation

Make sure you have [ROS 2 Humble](https://docs.ros.org/en/humble/index.html) and Ignition Gazebo installed.

### 1. Clone the Repository
```bash
git clone https://github.com/darshmenon/UR3_ROS2_PICK_AND_PLACE.git
cd UR3_ROS2_PICK_AND_PLACE
```

### 2. Install ROS Dependencies
```bash
sudo apt install ros-humble-rviz2 \
                 ros-humble-joint-state-publisher \
                 ros-humble-robot-state-publisher \
                 ros-humble-ros2-control \
                 ros-humble-ros2-controllers \
                 ros-humble-controller-manager \
                 ros-humble-joint-trajectory-controller \
                 ros-humble-position-controllers \
                 ros-humble-gz-ros2-control \
                 ros-humble-ros2controlcli \
                 ros-humble-moveit \
                 ros-humble-cv-bridge \
                 ros-humble-tf2-ros \
                 ros-humble-tf2-geometry-msgs
```

### 3. Install Python Dependencies
```bash
pip3 install -r requirements.txt
# anthropic is required for the LLM planner:
export ANTHROPIC_API_KEY=your_key_here
```

### 4. Build the Workspace
```bash
colcon build --symlink-install
source install/setup.bash
```

---

## 🧩 MoveIt Task Constructor Setup

To enable advanced pick-and-place planning with MoveIt 2, this project supports [MoveIt Task Constructor (MTC)](https://github.com/ros-planning/moveit_task_constructor).  
Instead of duplicating the full setup process, we've included a detailed guide in a separate submodule:

📄 **Follow the MTC installation and patching guide here:**  
[`ur_mtc_pick_place_demo/README.md`](ur_mtc_pick_place_demo/README.md)

This includes:
- Cloning the correct MTC branch and commit
- Installing dependencies
- Fixes for planning scene execution issues
- Rebuild instructions

Once complete, you'll be ready to run scripted and interactive pick-and-place pipelines using MTC!

---

## 🚀 Launch Instructions

### Launch Full Simulation in Gazebo
```bash
ros2 launch ur_gazebo ur.gazebo.launch.py
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

## 🤖 Move the Arm from CLI

Send a simple trajectory:
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

## 🔁 Run Arm-Gripper Automation Script

Run a full pick-return-release loop:
```bash
python3 ~/UR3_ROS2_PICK_AND_PLACE/ur_system_tests/scripts/arm_gripper_loop_controller.py
```

---

## ⚡ Custom Zig-Zag Motion Demo
To run the custom Cartesian (LIN) zig-zag motion demo using the MoveIt 2 PILZ Industrial Motion Planner:
```bash
ros2 run ur_moveit_demos custom_zigzag_motion
```
*Note: Make sure the Gazebo simulation (`ur.gazebo.launch.py`) has been running for at least 60 seconds so all controllers are initialized before starting the node.*

---

## 📝 MTC Demo Script

To run the full MTC demo with the UR3 and Robotiq gripper, execute the following steps:

### 1. **Make the Bash Script Executable**
```bash
chmod +x ~/UR3_ROS2_PICK_AND_PLACE/ur_mtc_pick_place_demo/scripts/robot.sh
```

### 2. **Run the Script**
Execute the script to launch the complete simulation:
```bash
~/UR3_ROS2_PICK_AND_PLACE/ur_mtc_pick_place_demo/scripts/robot.sh
```

This script will:
- Launch the **Gazebo** simulation with the UR3 robot and gripper.
- Launch **MoveIt 2** with the necessary configurations for pick-and-place tasks.
- Adjust the **camera position** in the simulation.
- Start the **Pick-and-Place demo** with MTC.

---

## 📸 Screenshots

### UR3 with Robotiq Gripper in RViz  
![Arm with Gripper](/images/arm_with_gripper.png)

### Robotiq Gripper Close-up  
![Gripper](/images/gripper.png)

### Simulation in Gazebo  
![Gazebo View](/images/image.png)

### RViz Overview  
![RViz 1](/images/rviz1.png)

### mtc Overview  
![MC](/images/mtc.png)

### mtc Overview  

![pick error](images/pick_error.png)

### mtc Pipline  

![alt text](images/mtc_pp.png)

### loop
![alt text](images/looponline-video-cutter.com-ezgif.com-video-to-gif-converter.gif)


---

## 🤖 AI / ML Stack

Three new packages extend the project with autonomous perception and planning:

### Vision-Based Perception (`ur_perception`)
Color + optional YOLO object detection from the onboard Intel D435 camera. Detects red/green/blue/yellow objects, estimates 3D pose via depth + TF2, and publishes them to the MoveIt planning scene automatically.

```bash
ros2 launch ur_perception perception.launch.py
# Watch detections:
ros2 topic echo /detected_objects
# View annotated camera feed in RViz: /detection_image
```

### LLM Task Planning (`ur_llm_planner`)
Natural language → robot motion. Send a plain English command and Claude figures out the pick-and-place sequence.

```bash
export ANTHROPIC_API_KEY=your_key_here
ros2 launch ur_llm_planner llm_planner.launch.py

# Send a command:
ros2 topic pub --once /llm_planner/command std_msgs/msg/String \
  "{data: 'pick up the red block and place it in the left bin'}"
```

### Demonstration Recording + Behavior Cloning (`ur_data_collector`)
Record robot demonstrations to HDF5 files, then train a BC policy.

```bash
# Start recording
ros2 launch ur_data_collector data_collector.launch.py
ros2 service call /data_collector/start_recording std_srvs/srv/Trigger
# ... run a demo ...
ros2 service call /data_collector/stop_recording std_srvs/srv/Trigger

# Train BC policy
python3 ur_data_collector/scripts/train_bc.py \
  --data_dir ~/ur3_demos \
  --output_dir ~/bc_policy \
  --epochs 50
```

### Full Demo (all-in-one)
```bash
# Launches Gazebo + MoveIt + perception automatically
ros2 launch ur_gazebo full_demo.launch.py

# With LLM planner enabled:
ros2 launch ur_gazebo full_demo.launch.py use_llm_planner:=true

# Use the new colored blocks world (default):
ros2 launch ur_gazebo full_demo.launch.py world:=colored_blocks.world
```

---

## 🤝 Contributing

Feel free to open pull requests or issues if you have improvements or bug reports.


