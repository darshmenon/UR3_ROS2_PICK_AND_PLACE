
# UR Robotic Arm with Robotiq 2-Finger Gripper for ROS 2

Related Blog Post: For behind-the-scenes details and the full development journey, check out the companion Medium article:
[How I'm Building an Autonomous Pick-and-Place System with ROS 2 Jazzy and Gazebo Harmonic](https://medium.com/@darshmenon02/how-i-am-building-an-autonomous-pick-and-place-system-with-ros-2-jazzy-and-gazebo-harmonic-6474cbcc8dc7)

The blog dives into simulation setup, robotic control, MoveIt Task Constructor, and lessons learned — perfect if you're curious about the engineering side or want to replicate the project from scratch.

This project integrates the Robotiq 2-Finger Gripper with a Universal Robots UR3 arm using **ROS 2 Humble** and **Gazebo Harmonic**. It includes URDF models, ROS 2 control configuration, simulation launch files, MoveIt Task Constructor pick-and-place, vision-based object detection, LLM-driven task planning (Ollama), and demonstration recording for behavior cloning.

---

## Demo

![alt text](assets/exec.gif)

![alt text](<assets/gazebo_simonline-video-cutter.com-ezgif.com-video-to-gif-converter (1).gif>)

---

## Installation

Make sure you have [ROS 2 Humble](https://docs.ros.org/en/humble/index.html) and **Gazebo Harmonic** (`gz-sim` 8.x) installed. Ignition Fortress (`ign gazebo` / gz-sim 6) will not work — the world file and bridge packages are Harmonic-specific.

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
pip3 install py-trees          # required for ur_bt_planner
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
# Default — Robotiq 2F-85
ros2 launch ur_gazebo ur.gazebo.launch.py

# Robotiq 2F-140
ros2 launch ur_gazebo ur.gazebo.launch.py gripper:=robotiq_2f_140

# OnRobot RG2
ros2 launch ur_gazebo ur.gazebo.launch.py gripper:=onrobot_rg2

# OnRobot RG6
ros2 launch ur_gazebo ur.gazebo.launch.py gripper:=onrobot_rg6

# Wrist-mounted camera (eye-in-hand) instead of the fixed head camera
ros2 launch ur_gazebo ur.gazebo.launch.py wrist_camera:=true
```

---

## Supported Grippers

| Gripper | Arg | Actuated joint | Mimic joints |
|---|---|---|---|
| Robotiq 2F-85 | `robotiq_2f_85` | `finger_joint` | 5 |
| Robotiq 2F-140 | `robotiq_2f_140` | `finger_joint` | 5 |
| OnRobot RG2 | `onrobot_rg2` | `gripper_joint` | 5 |
| OnRobot RG6 | `onrobot_rg6` | `gripper_joint` | 5 |

All four grippers use `position_controllers/GripperActionController` for the single commanded joint. Mimic joints are state-only — Gazebo Harmonic enforces the `<mimic>` constraints at the physics level.

### Verify Controllers After Launch

Controllers spawn sequentially (each one starts only after the previous finishes, to avoid racing `controller_manager`) and take ~10-15 s. Run this to confirm all three are `active`:

```bash
ros2 control list_controllers
```

Expected output (same for all grippers):

```
arm_controller[joint_trajectory_controller/JointTrajectoryController] active
gripper_controller[position_controllers/GripperActionController] active
joint_state_broadcaster[joint_state_broadcaster/JointStateBroadcaster] active
```

### Command the Gripper from CLI

**Robotiq (2F-85 / 2F-140)** — `finger_joint` range `0.0` (open) → `0.8` (closed):

```bash
ros2 action send_goal /gripper_controller/gripper_cmd \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.5, max_effort: 50.0}}"
```

**OnRobot (RG2 / RG6)** — `gripper_joint` range `0.0` (open) → `1.3` (closed):

```bash
ros2 action send_goal /gripper_controller/gripper_cmd \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.65, max_effort: 50.0}}"
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

## Full Autonomous Pipeline

`full_demo.launch.py` brings up the entire stack — Gazebo, MoveIt, perception, grasp detection, and a selectable autonomous brain — in a single command.

```bash
source install/setup.bash

# LLM planner (Ollama, send commands via /llm_planner/command):
ros2 launch ur_gazebo full_demo.launch.py brain:=llm

# Trained SAC policy (auto-reads object position from perception):
ros2 launch ur_gazebo full_demo.launch.py brain:=rl \
  model_path:=ur_rl_training/models/checkpoints/<run>/best_model.zip

# OpenVLA end-to-end vision-language-action:
ros2 launch ur_gazebo full_demo.launch.py brain:=openvla \
  task:="pick the red block and place it in the bin"

# Perception + grasp only (no autonomous control):
ros2 launch ur_gazebo full_demo.launch.py brain:=none
```

Startup sequence: Gazebo + MoveIt → perception (60 s) → grasp (62 s) → brain (65 s).

### Pipeline Data Flow

```
Camera/Depth  →  ur_perception  →  /detected_objects  →  LLM planner
                                                       →  RL policy (auto object tracking)
PointCloud2   →  ur_grasp       →  /ur_grasp/grasp_pose → RL policy (overrides perception)
Camera        →  OpenVLA        →  /arm_controller/joint_trajectory
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
python3 ur_system_tests/scripts/gui.py
```

---

## UR3 Reinforcement Learning (SAC)

Trains a Soft Actor-Critic (SAC) policy in MuJoCo and deploys it to Gazebo. The policy learns to reach, grasp, lift, and place a cube using the UR3 + Robotiq 2F-85.

**Features:**
- VecNormalize observation and reward normalisation for stable training
- 4-phase curriculum: reach → grasp → lift → place; auto-advances to full task once eval reward ≥ 400
- Phase-distribution and success-rate metrics logged to TensorBoard every eval interval
- Domain randomisation: object mass, friction, size (±20%), observation noise, joint jitter

**Train:**

```bash
cd ur_rl_training
python3 scripts/train.py --timesteps 3000000
# Resume from checkpoint (loads vecnormalize.pkl automatically):
python3 scripts/train.py --resume models/checkpoints/<run>/best_model
```

Best model and normalisation stats saved to `ur_rl_training/models/checkpoints/<run>/`.

**View policy in Gazebo:**

```bash
# Terminal 1 — Gazebo + MoveIt:
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py world_file:=rl_policy_demo.world

# Terminal 2 — RL policy node:
source install/setup.bash
ros2 launch ur_rl_training rl_policy.launch.py \
  model_path:=ur_rl_training/models/checkpoints/<run>/best_model.zip
```

Optional launch parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `action_scale` | `0.1` | Joint delta per step (increase for faster motion, e.g. `0.4`) |
| `step_dt` | `0.01` | Trajectory point duration in seconds |
| `control_rate_hz` | `100.0` | Policy inference rate |
| `object_x/y/z` | `0.35/0.0/0.045` | Object position fallback (auto-overridden by `/detected_objects` or `/ur_grasp/grasp_pose` when running) |
| `drop_x/y/z` | `0.35/0.20/0.02` | Drop zone position |
| `phase` | `1.0` | Curriculum phase (0=reach, 1=grasp, 2=lift, 3=place) |

**Headless evaluation:**

```bash
python3 ur_rl_training/scripts/eval_headless.py \
  --model ur_rl_training/models/checkpoints/<run>/best_model.zip \
  --episodes 20
```

---

## Force Control / Compliant Grasping (`ur_force_control`)

Monitors `finger_joint` effort from `/joint_states` to detect contact during gripper closure. Stops the gripper automatically when force exceeds the configured threshold, giving soft compliant grasps without crushing fragile objects.

**Topics:**

| Topic | Type | Description |
|---|---|---|
| `/ft/finger_effort` | `std_msgs/Float32` | Raw finger joint effort [Nm] |
| `/ft/contact_detected` | `std_msgs/Bool` | True when effort > threshold |

**Service:** `/ft/compliant_close` (`std_srvs/Trigger`) — incrementally closes the gripper and stops on contact.

**Launch:**

```bash
source install/setup.bash
ros2 launch ur_force_control ft_monitor.launch.py
```

The `MotionExecutor` class also exposes `compliant_close_gripper(max_effort=5.0)` and `compliant_pick()` for use from any node.

### External Wrench Estimator (arm-level, for admittance control)

No wrist F/T sensor is modeled on this robot, so `external_wrench_estimator` estimates external force/torque at the end-effector from arm joint effort readings via a damped-least-squares Jacobian-transpose inverse (`F ≈ pinv_damped(Jᵀ) · τ_ext`), where `τ_ext` is measured joint effort minus a real gravity torque `g(q)` computed every cycle by [Pinocchio](https://github.com/stack-of-tasks/pinocchio) RNEA from the full-body URDF (gripper mass included). This is the building block for admittance/contact-based control on the arm, as opposed to `ft_monitor_node`'s gripper-only effort threshold.

**Limitations:** `g(q)` is a rigid-body model, not a measurement — it doesn't capture joint friction or PID steady-state error, so a repeatable residual (observed up to ~25 N away from the idle pose in testing) remains even at rest; `/ft/zero_wrench` trims that residual at the current pose, but it's a per-pose correction, not a global fix. The damping also rolls off near kinematic singularities (this robot's idle pose sits at the UR wrist singularity, `wrist_2_joint ≈ 0`) instead of blowing up, but readings are less trustworthy there.

**Fixed (2026-07-24):** `τ_ext` was computed as measured effort *minus* `g(q)`, the same sign bug found in `joint_impedance_controller` — corrected to measured effort *plus* `g(q)` to match. **Still unresolved:** live testing also found that `/joint_states` effort for these effort-interface joints doesn't reliably track the torque actually commanded through `forward_command_controller_effort` (seen off by up to ~15x with no consistent scale factor across joints) — likely a deeper gz_ros2_control state-readback issue that the sign fix alone can't correct, and probably a large contributor to the residual noted above. Needs further investigation before trusting absolute wrench values.

**Topics:**

| Topic | Type | Description |
|---|---|---|
| `/ft/estimated_wrench` | `geometry_msgs/WrenchStamped` | Estimated external force/torque at the end-effector |
| `/ft/arm_contact_detected` | `std_msgs/Bool` | True when estimated force norm > `force_threshold_n` |

**Service:** `/ft/zero_wrench` (`std_srvs/Trigger`) — trims the residual bias (friction/PID error not captured by the gravity model) at the current pose.

**Launch and use:**

```bash
# Terminal 1 — full simulation:
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py

# Terminal 2 — wrench estimator (wait for controllers to spawn first, ~10-15 s):
source install/setup.bash
ros2 launch ur_force_control wrench_estimator.launch.py

# Terminal 3 — watch the estimate:
ros2 topic echo /ft/estimated_wrench

# Trim residual bias at the arm's current pose (gravity is already compensated by
# the model — this corrects friction/PID error the model doesn't capture):
ros2 service call /ft/zero_wrench std_srvs/srv/Trigger {}

# Watch for a contact event (goes true when force norm > force_threshold_n):
ros2 topic echo /ft/arm_contact_detected
```

Parameters: `planning_group` (default `arm`), `publish_rate_hz` (`30.0`), `force_threshold_n` (`15.0`), `damping_lambda` (`0.05`).

### Joint Impedance Controller (arm-level, torque control)

Direct joint-space torque control: `τ = K(q_des − q) − D·q̇ + g(q)`, with `g(q)` computed every cycle by Pinocchio RNEA (same approach as `external_wrench_estimator`) so the arm doesn't sag under its own weight even at zero stiffness. The arm's raw `forward_command_controller_effort` is spawned inactive alongside `arm_controller`, so switching to torque control means explicitly deactivating position control and activating the effort command controller.

Equilibrium pose defaults to wherever the arm is when the node starts (hold-current-pose) and can be moved via a target topic or re-captured at any time.

**Topic:** `/joint_impedance_controller/target_positions` (`std_msgs/Float64MultiArray`) — 6 values, one per arm joint, in `joint_names` order.

**Service:** `/joint_impedance_controller/hold_current_pose` (`std_srvs/Trigger`) — re-latches the equilibrium pose to the arm's current position.

**Motion planning:** MoveIt planning/execution should use the normal `arm_controller`. The custom impedance node is not a `FollowJointTrajectory` action server; it holds or shifts an equilibrium pose through `/joint_impedance_controller/target_positions`. For planned motion, execute with `arm_controller`, then switch to `forward_command_controller_effort` when you want compliant hold/contact behavior.

**Launch and use:**

```bash
# Terminal 1 — full simulation:
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py

# Terminal 2 — start the impedance controller BEFORE switching interfaces, so it's
# already commanding valid torque the instant the switch happens:
source install/setup.bash
ros2 launch ur_force_control joint_impedance.launch.py

# Terminal 3 — hand control from arm_controller to the torque controller:
ros2 control switch_controllers --deactivate arm_controller --activate forward_command_controller_effort

# Move the equilibrium pose:
ros2 topic pub --once /joint_impedance_controller/target_positions std_msgs/msg/Float64MultiArray \
  "{data: [0.0, -1.57, 1.57, 0.0, 1.57, 0.0]}"

# Hand control back to position control when done:
ros2 control switch_controllers --deactivate forward_command_controller_effort --activate arm_controller
```

Parameters: `joint_names`, `stiffness` (default `[80, 80, 60, 15, 15, 15]`), `damping` (default `[8, 8, 6, 1.5, 1.5, 1.5]`), `effort_limits` (default `[56, 56, 28, 12, 12, 12]`, matching `ur.ros2_control.xacro`), `publish_rate_hz` (`200.0`), `debug_logging` (`false`), `debug_log_period_ms` (`200`).

**Debugging note:** enable `debug_logging` for one controlled run to print `q`, `qdot`, `target`, `gravity`, spring torque, damping torque, raw torque, clamped command torque, and saturation state. This is intended for diagnosing sign/unit issues in the effort-control loop.

**Fixed (2026-07-24):** the gravity feedforward term was applied with the wrong sign (`+ gravity(q)` instead of `- gravity(q)`), so commanding pure gravity feedforward (stiffness and damping both zero) doubled the joints' downward acceleration instead of canceling it — the arm collapsed faster than free-fall, with wrist joints spinning past ±2π into their limits. Verified live in Gazebo Harmonic: with the corrected sign, the arm now holds its pose under zero stiffness/damping (drift <0.001 rad over several seconds).

---

## Behavior Tree Task Planner (`ur_bt_planner`)

Replaces the flat task-list execution model with a hierarchical behavior tree ([py_trees](https://py-trees.readthedocs.io/)). Supports retry on IK failure via a Selector fallback, making pick-and-place more robust than a simple sequential loop.

**Tree structure:**
```
Sequence [pick_place]
  ├─ go_home
  ├─ Selector [pick_or_retry]
  │    ├─ Sequence [pick]   ← open → compliant_pick
  │    └─ Sequence [retry]  ← plain pick (IK fallback seed)
  └─ Sequence [place]
       ├─ place(x,y,z)
       └─ return_home
```

**Services:**

| Service | Description |
|---|---|
| `/bt/run_pick_place` | Execute one full pick-and-place BT cycle |
| `/bt/stop` | Abort after current leaf completes |

**Launch:**

```bash
source install/setup.bash
ros2 launch ur_bt_planner bt_planner.launch.py \
  pick_x:=0.35 pick_y:=0.0 pick_z:=0.05 \
  place_x:=0.15 place_y:=0.30 place_z:=0.08

# Trigger a cycle:
ros2 service call /bt/run_pick_place std_srvs/srv/Trigger {}
```

---

## Conveyor Belt Simulation (`ur_conveyor`)

Simulates a moving conveyor feeding colored boxes into the UR3 pick zone. The `conveyor_node` spawns random-color boxes at the belt entry (x ≈ 0.88 m), moves them toward the pick zone (x ≈ 0.35 m) via Gazebo pose updates, and publishes `/conveyor/object_ready` when a box arrives. Unpicked boxes are despawned after a configurable timeout.

**Topics / Services:**

| Interface | Description |
|---|---|
| `/conveyor/object_ready` | `String` — `"box_N color"` when box at pick zone |
| `/conveyor/picked` | `String` — publish box name to mark as picked |
| `/conveyor/start` | Trigger — start belt |
| `/conveyor/stop` | Trigger — stop belt |

**Launch (includes Gazebo with conveyor world):**

```bash
source install/setup.bash
ros2 launch ur_conveyor conveyor.launch.py \
  spawn_interval_s:=6.0 belt_speed:=0.06

# Start the belt:
ros2 service call /conveyor/start std_srvs/srv/Trigger {}
```

The `conveyor_sorting.world` includes a belt visual with friction-direction surface (objects slide along X), a green pick-zone marker, and three colored bins (red, green, blue).

---

## Contributing

Pull requests and issues are welcome, especially around simulation stability, transfer learning, and perception-to-action integration.

---

## Future Scope

- Improve MuJoCo-to-Gazebo transfer so learned grasping policies behave more consistently on the UR3 with the Robotiq gripper.
- Fine-tune OpenVLA on collected UR3 demonstrations for better sim-to-real performance.
- Real robot deployment — swap Gazebo hardware interface for the live UR3 driver and test trained policies on hardware.
- 6-DoF object pose estimation from depth camera for better grasp orientation.
- Extend the BT planner to handle multi-object sorting using the conveyor + perception pipeline together.

---

## Work in Progress

The following features are actively being developed and are not yet fully integrated.

### Grasp Detection (`ur_grasp`)

Point-cloud grasp estimation for tabletop objects from the Intel D435 depth stream. Note: `camera_head` is **not** a wrist/eye-in-hand camera — it's a simulated D435 fixed to a stand bolted to `base_link` (`ur_description/urdf/intel_rgbd_cam_d435.urdf.xacro`), so it doesn't move with the arm.

Verified live in Gazebo Harmonic (2026-07-30), full chain: camera → point cloud → colour-filtered centroid detection → base_link pose → visual servo → gripper close.

- camera publishes real RGB, depth, and `PointCloud2` data (`/camera_head/color/image_raw`, `/camera_head/depth/image_rect_raw`, `/camera_head/depth/color/points`) at ~3-6 Hz
- `colour:=red` detection now returns an accurate `base_link`-frame pose (verified against Gazebo's ground-truth object pose, error < 2 cm)

**Fixed (2026-07-30):**
- `cylinder_grasp_detector.decode_pointcloud2` crashed `grasp_node` on every real detection request — `sensor_msgs_py.point_cloud2.read_points()` returns a structured numpy array on this ROS distro, and casting it straight to `float32` raised `TypeError`, killing the node. Switched to `read_points_numpy()`.
- `grasp_node`'s `colour` parameter was cached once in `__init__` and never re-read, so `ros2 param set /grasp_node colour red` (as documented below) silently had no effect. Now re-read from the parameter server on every detection.
- The real reason detection found nothing even with the colour fix: `estimate_cylinder_grasp()`'s workspace filters (table height, reach radius) are documented as base_link-frame bounds, but `grasp_node` ran them on the raw camera-frame cloud *before* transforming to base_link — camera-frame Z is depth, not height, so every real point was rejected. `grasp_node` now transforms the whole cloud to `base_link` first.
- `camera_tilt_angle_deg` in the D435 xacro was `25`, aiming the camera mostly at the far wall/floor — the table and object were outside its vertical FOV. Raised to `55` so the workspace is actually in frame (confirmed visually by dumping a camera frame to PNG).

**Fixed (2026-08-01):**
- `ur_visual_servo` tracked `tool0` directly as the grasp point — the Robotiq 2F-85 fingertip sits ~0.145 m along `tool0`'s +Z, so the arm reached the right height but closed ~0.12 m away in X/Y. `servo_node.py` now servos a virtual TCP (`tool0_origin + R_tool0 * tcp_offset_xyz`) instead of `tool0` — see `_ee_to_tcp`/`_tcp_to_ee`.

**Fixed (2026-08-02):**
- The LLM-planner/BT-planner/sorting-demo pick-and-place path had no TCP offset at all — `motion_executor.py`'s `_make_downward_pose()` drove `tool0` straight to the object's raw height, putting the fingertips ~0.145 m too low. Fixed with the same offset convention (`GRIPPER_TCP_OFFSET_Z = 0.145`) at every pick/place call site.

Launch:

```bash
source install/setup.bash
ros2 run ur_grasp grasp_node

# Or with optional args (colour filter and backend):
ros2 launch ur_grasp grasp_detection.launch.py colour:=red backend:=auto
```

Trigger one detection:

```bash
ros2 service call /ur_grasp/detect std_srvs/srv/Trigger {}
```

Healthy signs:

- advertises `/ur_grasp/detect`
- subscribes to `/camera_head/depth/color/points`
- publishes `/ur_grasp/grasp_pose`
- publishes `/ur_grasp/grasp_marker` for RViz
- falls back to the built-in numpy centroid detector if `simple_grasping` is not installed
- warns and returns no grasp if a point cloud has not arrived yet

#### Wrist-Mounted Camera Option (2026-07-30)

A second D435 mount is available, bolted to `tool0` (eye-in-hand) instead of
the fixed head stand described above:

- `ur_description/urdf/intel_rgbd_cam_d435_wrist.urdf.xacro` — the camera itself
- `ur_description/urdf/ur_wrist_cam.urdf.xacro`, `moveit_config/config/ur_wrist_cam.{urdf,srdf}.xacro` — full-robot variants that include it instead of the head camera (the originals are untouched)
- publishes on `/camera_wrist/*` (same topic shapes as `/camera_head/*`)

Launch with it instead of the head camera:

```bash
ros2 launch ur_gazebo ur.gazebo.launch.py wrist_camera:=true
```

`grasp_node` can target either camera via a parameter (default is now the
wrist camera):

```bash
ros2 launch ur_grasp grasp_detection.launch.py colour:=red \
  camera_topic:=/camera_wrist/depth/color/points \
  continuous_detect_hz:=0.0
```

Verified live (2026-07-30): the sensor is correctly attached under
`wrist_3_link` in the gz scene graph (fixed-joint lumping disabled on that
joint specifically, matching the pattern already used for the gripper
joint), and `/camera_wrist/depth/color/points` / `color/image_raw` stream
real data. Detection itself works well (100% confidence, 3000+ points)
**once the arm is already posed so the wrist camera can see the table** —
from the arm's default home pose the wrist camera only sees the gripper
itself, since it's rigidly mounted a few cm from it. This is a real
eye-in-hand geometry constraint, not a bug: a wrist camera can't bootstrap
detection from an arbitrary pose the way a fixed head camera can.

Two more findings from testing the full servo loop with this camera:

- `continuous_detect_hz > 0` (re-detecting every camera frame during the
  approach) is **not stable yet** — as the arm gets closer, the box's
  framing/point count in view changes a lot, and the recomputed grasp pose
  drifted several cm between frames. That moving target sent the servo loop
  into a wrong IK branch and it drove away from the object instead of
  converging. Leave `continuous_detect_hz:=0.0` (one-shot detection, frozen
  target) for now.
- Separately, even with a frozen target, `servo_node`'s incremental-step PBVS
  loop plateaus a few cm short of the target and hits `max_iterations`
  without ever closing the gap — the final direct "descend to grasp" jump
  (which isn't constrained to a small step from the previous pose) still
  reaches the correct pose fine. This looks like IK-branch jumping between
  successive tiny Cartesian steps, not anything camera-specific.
- The final grasp itself did not succeed (verified by commanding the arm to
  lift afterward — the box stayed on the table) — consistent with the
  tool0-vs-actual-fingertip offset already logged as a known limitation
  above, reproduced here via the wrist camera path too.

### Vision-Based Perception (`ur_perception`)

Color-based object detection with optional YOLO and PCL cluster extraction from the Intel D435 camera.

Launch:

```bash
source install/setup.bash
ros2 launch ur_perception perception.launch.py
```

Watch detections:

```bash
ros2 topic echo /detected_objects
```

#### Multi-View 3D Reconstruction (2026-07-30)

`object_reconstructor_node` fuses point cloud frames from a moving camera into
a single accumulated cloud, using TF (not ICP) for registration — the wrist
camera's pose relative to `base_link` is already known exactly from forward
kinematics, so each frame just gets transformed into `base_link` and merged
into a voxel grid. Moving the arm around an object fills in the occlusions any
single fixed viewpoint would miss.

**This is a standalone perception/inspection tool** — nothing in the pick-and-place
pipeline consumes `/ur_perception/reconstructed_points` yet (`ur_grasp` still
detects grasps off a single raw frame, and `object_reconstructor_node` only
*listens* to `/ur_grasp/grasp_pose` to auto-recenter its ROI). Use it to build
and export a fused point cloud for inspection; it won't by itself sharpen the
grasp the arm executes.

Two things that will give you zero fused points if missed — the node now logs
a `warn` every 3s while active and stuck at zero, naming which of these it is,
instead of silently sitting at "0 frames" forever:

- **The wrist camera must be launched with `wrist_camera:=true`** — it's opt-in
  (default `false`), so `/camera_wrist/depth/color/points` won't exist at all
  without it. Shows up as: `no messages received on '<topic>' yet — is the
  wrist camera launched...?`.
- **The arm has to actually be pointed at the object.** The default `home` pose
  aims the wrist camera up and away from the table — the reconstructor will
  merge nothing until the arm is at a pose (e.g. a pre-grasp hover over the
  object) that puts the target inside `roi_radius` of `roi_center`. Shows up
  as: `frame(s) received but 0 merged ... is the arm pointed so the camera
  sees roi_center=...?`.

```bash
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py wrist_camera:=true
# ...move the arm so the wrist camera is looking at the object...

ros2 launch ur_perception reconstruct.launch.py \
  camera_topic:=/camera_wrist/depth/color/points \
  roi_radius:=0.20 \
  save_path:=/tmp/object.ply

ros2 service call /ur_perception/reconstruct/start std_srvs/srv/Trigger {}
# ...move the arm / let the wrist camera sweep the object...
ros2 service call /ur_perception/reconstruct/stop std_srvs/srv/Trigger {}
```

Live fused cloud publishes on `/ur_perception/reconstructed_points`
(`base_link` frame) while accumulating, viewable in RViz. The service response
reports `saved to <path>` once `stop` finishes writing the PLY — check for that
line if you passed `save_path`.

Verified live (2026-07-30): swept the arm through 5 waypoints around the red
box with the wrist camera, accumulated 154 frames into 35k voxels, and wrote a
valid ASCII PLY (`open(path).readlines()` + point count round-tripped
correctly). The `roi_radius` filter is a plain sphere around either a fixed
`roi_center` param or the last `/ur_grasp/grasp_pose` (auto-recenters if
`ur_grasp` is running) — it keeps the table and any nearby clutter in frame
too, not just the target object, so don't expect an isolated single-object
mesh out of the box.

Re-verified live (2026-07-31), holding a single pre-grasp hover pose over the
box (no sweep): merged 44 of ~50 possible frames in 5s at the camera's 10Hz
into 2400 voxels, PLY round-tripped correctly. `VoxelMap.add()` used to merge
points one at a time in a Python loop — at the wrist camera's ~70k points/frame
that was slow enough to starve this node's own TF listener (same
single-threaded executor), so most frames failed their TF lookup and got
silently dropped (1-2 frames actually merged per 5s window, not ~50). Fixed
by vectorising the voxel merge with numpy.

Re-verified live (2026-08-01): a 5cm test cube came out ~11cm elongated in a
5-view sweep. Cause: the stamped TF lookup only got 0.05s, so most frames fell
back to a stale "latest" transform instead of the pose at actual capture time,
smearing points along the arm's motion. Fixed by widening that timeout to 0.2s
(`tf_fail` dropped from ~65% of frames to 0) and tightening `max_tf_age_sec`
0.25 → 0.05 as a backstop. Confirmed: a single stationary viewpoint now
reconstructs the cube at 4.8x4.85x4.63cm — matches the true 5cm within a voxel.

**Known limitation**: multi-view fusion still shows a few cm of spread on one
axis, since registration is TF-based, not ICP — each viewpoint's depth reading
has its own small bias, and nothing reconciles that across views. Real
accuracy ceiling of this approach, not a bug; closing it needs an ICP
registration pass, not a parameter tweak.

Run the node directly:

```bash
source install/setup.bash
ros2 run ur_perception object_reconstructor_node.py
```

#### Viewing the camera feed

To see what either camera (`camera_head` or `camera_wrist`) is actually
looking at, without needing RViz:

```bash
source install/setup.bash
ros2 run rqt_image_view rqt_image_view /camera_wrist/color/image_raw
# or: /camera_head/color/image_raw
```

To add it in RViz instead (already open from `ur.gazebo.launch.py`):

1. Bottom-left **Displays** panel → **Add** button.
2. Pick the **By topic** tab, not **By display type** — it lists only topics
   that currently have data, so you can't pick the wrong message type by accident.
3. Expand `/camera_wrist` (or `/camera_head`) and choose:
   - `color/image_raw` → **Image** — adds a separate 2D image panel showing the RGB feed.
   - `depth/color/points` → **PointCloud2** — adds the raw 3D depth cloud into the main 3D view.
   - (once reconstruction is running) `/ur_perception/reconstructed_points` → **PointCloud2** — the fused, accumulated cloud.
4. Click **OK**. If a `PointCloud2` display stays empty, check the **Global
   Options → Fixed Frame** at the top of the Displays panel is set to
   `base_link` — a cloud published in a different frame than the fixed frame
   won't render.

Verified in this workspace:

- package imports successfully after `source install/setup.bash`
- installed executable: `ros2 run ur_perception object_detector_node.py`

Healthy signs:

- publishes detected objects on `/detected_objects`
- publishes annotated images on `/detection_image`
- publishes collision objects on `/planning_scene`
- waits for `/camera_head/color/image_raw`, `/camera_head/depth/image_rect_raw`, and `/camera_head/camera_info`
- warns and keeps color detection enabled if `use_yolo:=true` is set but `ultralytics` is missing

### LLM Task Planner (`ur_llm_planner`)

Natural-language task planning backed by a local Ollama model and connected to perception plus the MoveIt/gripper execution path.

Verified in this workspace:

- package imports successfully after `source install/setup.bash`
- installed executable: `ros2 run ur_llm_planner llm_planner_node.py`
- command topic exists in code at `/llm_planner/command`
- planner converts text into a JSON task list and passes it to `MotionExecutor`

Launch:

```bash
source install/setup.bash
ros2 run ur_llm_planner llm_planner_node.py
```

Or use the launch file:

```bash
source install/setup.bash
ros2 launch ur_llm_planner llm_planner.launch.py
```

Send a text instruction:

```bash
ros2 topic pub --once /llm_planner/command std_msgs/msg/String \
  "{data: 'pick up the red object and place it to the left of the robot'}"
```

Healthy signs:

- subscribes to `/detected_objects`
- listens on `/llm_planner/command`
- asks Ollama for a JSON task plan
- executes actions like `move_to_named_pose`, `pick`, `place`, `open_gripper`, and `close_gripper`
- retries up to 2 times on execution failure, sending failure context back to the LLM for a simpler re-plan
- warns and returns an empty task list if Ollama is not available at `http://localhost:11434`
- may plan successfully but fail execution if MoveIt or gripper action servers are unavailable

Ollama setup:

```bash
ollama serve
ollama pull llama3.2:3b
ros2 launch ur_llm_planner llm_planner.launch.py ollama_model:=llama3.2:3b
```
