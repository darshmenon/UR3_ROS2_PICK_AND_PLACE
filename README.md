
# UR Robotic Arm with Robotiq 2-Finger Gripper for ROS 2

Blog post (dev journey, engineering details): [How I'm Building an Autonomous Pick-and-Place System with ROS 2 Jazzy and Gazebo Harmonic](https://medium.com/@darshmenon02/how-i-am-building-an-autonomous-pick-and-place-system-with-ros-2-jazzy-and-gazebo-harmonic-6474cbcc8dc7)

Integrates the Robotiq 2-Finger Gripper with a UR3 arm on **ROS 2 Humble** + **Gazebo Harmonic**: URDF models, ros2_control config, simulation launch files, MoveIt Task Constructor pick-and-place, vision-based object detection, LLM-driven task planning (Ollama), and demonstration recording for behavior cloning.

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
source install/setup.bash
bash ur_mtc_pick_place_demo/scripts/robot.sh              # GUI
USE_GAZEBO_GUI=false bash ur_mtc_pick_place_demo/scripts/robot.sh   # headless
```

Or two terminals (`ROS_DOMAIN_ID` must match; default `113`):

```bash
# T1
export ROS_DOMAIN_ID=113 ROS_LOCALHOST_ONLY=1 GZ_VERSION=harmonic
export GZ_SIM_SYSTEM_PLUGIN_PATH="$(ros2 pkg prefix gz_ros2_control)/lib:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"
ros2 launch ur_gazebo ur.gazebo.launch.py \
  world_file:=pick_and_place_demo.world gripper:=robotiq_2f_85 \
  use_rviz:=false use_move_group:=true use_gazebo_gui:=true

# T2 — after /get_planning_scene + arm/gripper controllers are up
export ROS_DOMAIN_ID=113 ROS_LOCALHOST_ONLY=1
ros2 launch ur_mtc_pick_place_demo pick_place_demo.launch.py
```

Success: `Task executed successfully`. Cold-stack execute `-3` → retry T2.

`robot.sh` also starts `get_planning_scene_server` before MTC. Manual two-terminal flow: launch it between T1 and T2:

```bash
ros2 launch ur_mtc_pick_place_demo get_planning_scene_server.launch.py
```

### Planning scene server (object + table from the camera)

`get_planning_scene_server` turns the head depth cloud into MoveIt collision objects so MTC knows **what** to pick and **where** it is.

Flow:
1. Subscribes to `/camera_head/depth/color/points` (+ RGB), crops to the pick workspace (`crop_min_z: 0.02` drops the big `mount_table` at z≈0).
2. RANSAC plane → `support_surface` (pick table). Rejects planes with top face below `support_min_z`.
3. Remaining points → clusters; RANSAC cylinder/box fit → collision objects in `base_link`.
4. Service `/get_planning_scene_ur` (`ur_interfaces/GetPlanningScene`): request `target_shape` + `target_dimensions`; response has `scene_world`, `target_object_id`, `support_surface_id`.

`mtc_node` calls that service at startup, applies the objects into MoveIt’s planning scene, then builds the pick/place task around `target_object_id`. If perception fails (or `force_fallback_scene:=true`), it installs a known table+cylinder instead.

```bash
ros2 launch ur_mtc_pick_place_demo get_planning_scene_server.launch.py
# then MTC (or robot.sh, which starts both)
```

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

# Empty floor + red cylinder only (no table) — for MotionPlanning / pick-and-place tests
ros2 launch ur_gazebo ur.gazebo.launch.py \
  world_file:=empty_red_cylinder.world \
  table_height:=0.0 \
  use_rviz:=true \
  use_move_group:=true \
  use_gazebo_gui:=true
```

| World | Table | Objects |
|---|---|---|
| `empty.world` | no | none |
| `empty_red_cylinder.world` | no (`table_height:=0.0`) | red cylinder only at `(0.36, 0, 0.06)` |
| `pick_and_place_demo.world` | yes (`table_height` default `1.015`) | red cylinder + YCB props |

### Interactive MoveIt 2 Planning in RViz

`ur.gazebo.launch.py` already starts **move_group** + **RViz** (`use_rviz:=true`, `use_move_group:=true` by default) with pipelines **`ompl`** (default) and **`pilz_industrial_motion_planner`**.

#### How to use (quick start)

Recommended test scene (empty floor + red cylinder, no table):

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash

ros2 launch ur_gazebo ur.gazebo.launch.py \
  world_file:=empty_red_cylinder.world \
  table_height:=0.0 \
  use_rviz:=true \
  use_move_group:=true \
  use_gazebo_gui:=true
```

Wait ~15 s for controllers, then in RViz **MotionPlanning**:

1. **Planning Group** → `arm` (prefer this over `arm_with_gripper` for free-space tests).
2. **Context** → Planning Library → `OMPL`.
3. **Planning** → Planner → `RRTConnectkConfigDefault`.
4. Drag the orange interactive marker to a reachable goal (avoid folding into the torso).
5. Click **Plan & Execute** (or **Plan**, then **Execute** right away).

You should see one solid robot (current state) and one ghost/orange robot (query goal) — that is normal, not two arms.

OMPL trajectories are time-stamped by **TOTG** (`AddTimeOptimalParameterization` in `moveit_config/config/ompl_planning.yaml`). Without that adapter, `arm_controller` rejects Execute with `Time between points ... not strictly increasing`.

**If Execute fails**

| Symptom | Fix |
|---|---|
| `start point deviates from current robot state` | Re-**Plan** then **Execute** (stale plan after the arm moved) |
| `Computed path is not valid` / self-collision | Soften the goal; use `RRTConnectkConfigDefault`, not a colliding pose |
| `No ContextLoader for planner_id ''` | Using Pilz — set Planner to `LIN`, `PTP`, or `CIRC` |
| RViz `Detected jump back in time` / segfault | Kill duplicate Gazebo/RViz stacks; launch **one** full command above |

#### Launch for interactive control

```bash
source /opt/ros/$ROS_DISTRO/setup.bash
source install/setup.bash

# Full stack: Gazebo + move_group + RViz (plan/execute from MotionPlanning)
ros2 launch ur_gazebo ur.gazebo.launch.py \
  use_rviz:=true \
  use_move_group:=true \
  use_gazebo_gui:=true

# Headless Gazebo GUI, keep MoveIt RViz for planning
ros2 launch ur_gazebo ur.gazebo.launch.py \
  use_rviz:=true \
  use_move_group:=true \
  use_gazebo_gui:=false

# Sim already running without RViz — attach RViz only
ros2 launch moveit_config move_group.launch.py \
  use_move_group:=false \
  use_rviz:=true \
  use_sim_time:=true

# MoveIt + RViz only (no Gazebo; useful if robot/controllers are already up)
ros2 launch moveit_config move_group.launch.py \
  use_move_group:=true \
  use_rviz:=true \
  use_sim_time:=true
```

Useful launch args on `ur.gazebo.launch.py`:

| Arg | Default | Control |
|---|---|---|
| `use_rviz` | `true` | Start RViz with MotionPlanning |
| `use_move_group` | `true` | Start MoveIt `move_group` (needed to Plan/Execute) |
| `use_gazebo_gui` | `true` | Gazebo client window |
| `gripper` | `robotiq_2f_85` | Gripper model |

After launch, wait ~10–15 s then confirm controllers:

```bash
ros2 control list_controllers
```

You should see `arm_controller` and `gripper_controller` **active**. Cartesian planning uses `/compute_cartesian_path`; joint planning uses `/move_action`.

In RViz, open the **MotionPlanning** panel (Displays → MotionPlanning):

1. **Planning Group** → `arm` (or `gripper`).
2. Drag the interactive marker to a goal pose (or use **Query** → random/valid goal).
3. **Plan** then **Execute** (or **Plan & Execute**).

#### OMPL + RRTConnect (joint-space)

Default pipeline is OMPL; default planner for `arm` is **`RRTConnectkConfigDefault`**.

| Control | Where in RViz MotionPlanning |
|---|---|
| Pipeline | **Context** tab → Planning Library → `OMPL` |
| Planner | **Planning** tab → Planner → `RRTConnectkConfigDefault` (or others: `RRTkConfigDefault`, `RRTstarkConfigDefault`, `LBKPIECEkConfigDefault`, …) |
| Time / attempts | **Planning** tab → Planning Time / Planning Attempts |

Configs live in `moveit_config/config/ompl_planning.yaml`.

#### Cartesian path planning (how to control it)

Cartesian mode moves the **end-effector in a (near) straight line in XYZ**, instead of OMPL wandering in joint space. Two ways:

**A. RViz → MotionPlanning → Cartesian Path tab** (recommended for interactive control)

```bash
ros2 launch ur_gazebo ur.gazebo.launch.py
```

1. In RViz, select the **MotionPlanning** panel (bottom or side panel).
2. **Planning Group** = `arm`.
3. Open the **Cartesian Path** tab (next to Context / Planning / Query).
4. Suggested settings:
   - **Cart. step size** ≈ `0.01` (1 cm); smaller = denser/slower path
   - **Jump threshold** ≈ `0.0` (reject discontinuous IK jumps) or `2.0` if planning fails
   - Check **Approx IK solutions** if exact IK fails on some waypoints
   - Uncheck **Avoid Collisions** only for debugging (keep it on normally)
5. Drag the interactive marker to the goal (or nudge X/Y/Z with the rings/arrows).
6. Click **Plan Cartesian Path** — status shows fraction succeeded (want `1.0`).
7. Click **Execute** to run it on the simulated arm.

If Plan Cartesian Path reports e.g. `0.4` (40%), the arm cannot reach a straight line all the way — shorten the goal or switch to OMPL/RRTConnect for that move.

**B. Pilz `LIN` planner** (same MotionPlanning panel, industrial Cartesian)

1. **Context** tab → Planning Library → `pilz_industrial_motion_planner`.
2. **Planning** tab → Planner → **`LIN`** (straight Cartesian). Use `PTP` for joint moves, `CIRC` for arcs.
3. Set goal with the marker → **Plan** → **Execute**.
4. Speed limits come from `moveit_config/config/pilz_cartesian_limits.yaml`.

**When to use which**

| Goal | Use |
|---|---|
| Straight approach / retreat / slide | Cartesian Path tab or Pilz `LIN` |
| Around obstacles / free space | OMPL + `RRTConnectkConfigDefault` |
| Fast joint-space reorient | Pilz `PTP` or OMPL |

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

Monitors `finger_joint` effort to detect contact during gripper closure and stops before crushing the object.

| Topic | Type | Description |
|---|---|---|
| `/ft/finger_effort` | `std_msgs/Float32` | Raw finger joint effort [Nm] |
| `/ft/contact_detected` | `std_msgs/Bool` | True when effort > threshold |

Service: `/ft/compliant_close` (`std_srvs/Trigger`) — closes incrementally, stops on contact.

```bash
source install/setup.bash
ros2 launch ur_force_control ft_monitor.launch.py
```

Also exposed via `MotionExecutor.compliant_close_gripper(max_effort=5.0)` / `.compliant_pick()`.

### External Wrench Estimator (arm-level, for admittance control)

No wrist F/T sensor is modeled, so `external_wrench_estimator` infers external force/torque at the end-effector from arm joint effort: `F ≈ pinv_damped(Jᵀ) · τ_ext`, where `τ_ext` = measured effort − gravity torque `g(q)` (Pinocchio RNEA, full-body URDF).

**Limitations:** `g(q)` is a rigid-body model and doesn't capture friction/PID error, leaving a residual (up to ~25 N at rest in testing); `/ft/zero_wrench` trims it at the current pose only, not globally. Estimates are also less trustworthy near the wrist singularity (idle pose has `wrist_2_joint ≈ 0`).

**Status:** sign bug fixed 2026-07-24 (was `effort − g(q)`, now `effort + g(q)`). Still unresolved: `/joint_states` effort doesn't reliably track commanded torque (off by up to ~15x, inconsistent scale) — likely a gz_ros2_control readback issue, probably contributing to the residual above. Don't trust absolute wrench values yet.

| Topic | Type | Description |
|---|---|---|
| `/ft/estimated_wrench` | `geometry_msgs/WrenchStamped` | Estimated external wrench at the end-effector |
| `/ft/arm_contact_detected` | `std_msgs/Bool` | True when force norm > `force_threshold_n` |

Service: `/ft/zero_wrench` (`std_srvs/Trigger`) — trims residual bias at the current pose.

```bash
# Terminal 1 — sim:
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py

# Terminal 2 — estimator (after controllers spawn, ~10-15s):
ros2 launch ur_force_control wrench_estimator.launch.py

# Terminal 3:
ros2 topic echo /ft/estimated_wrench
ros2 service call /ft/zero_wrench std_srvs/srv/Trigger {}
ros2 topic echo /ft/arm_contact_detected
```

Params: `planning_group` (`arm`), `publish_rate_hz` (`30.0`), `force_threshold_n` (`15.0`), `damping_lambda` (`0.05`).

### Joint Impedance Controller (arm-level, torque control)

Joint-space torque control: `τ = K(q_des − q) − D·q̇ + g(q)`, `g(q)` via Pinocchio RNEA so the arm holds pose at zero stiffness. `forward_command_controller_effort` spawns inactive alongside `arm_controller` — switching to torque control means deactivating one and activating the other.

Equilibrium pose defaults to wherever the arm is on startup; movable via topic or re-latchable to current pose.

- Topic: `/joint_impedance_controller/target_positions` (`std_msgs/Float64MultiArray`, 6 values in `joint_names` order)
- Service: `/joint_impedance_controller/hold_current_pose` (`std_srvs/Trigger`)
- Use `arm_controller` for MoveIt planning/execution — the impedance node isn't a `FollowJointTrajectory` server. Switch to `forward_command_controller_effort` only for compliant hold/contact.

```bash
# Terminal 1 — sim:
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py

# Terminal 2 — start before switching interfaces:
ros2 launch ur_force_control joint_impedance.launch.py

# Terminal 3 — hand off control:
ros2 control switch_controllers --deactivate arm_controller --activate forward_command_controller_effort

ros2 topic pub --once /joint_impedance_controller/target_positions std_msgs/msg/Float64MultiArray \
  "{data: [0.0, -1.57, 1.57, 0.0, 1.57, 0.0]}"

# Hand back when done:
ros2 control switch_controllers --deactivate forward_command_controller_effort --activate arm_controller
```

Params: `joint_names`, `stiffness` (`[80, 80, 60, 15, 15, 15]`), `damping` (`[8, 8, 6, 1.5, 1.5, 1.5]`), `effort_limits` (`[56, 56, 28, 12, 12, 12]`, matches `ur.ros2_control.xacro`), `publish_rate_hz` (`200.0`), `debug_logging` (`false`), `debug_log_period_ms` (`200`).

`debug_logging` prints q, qdot, target, gravity, spring/damping/raw/clamped torque, and saturation state — useful for diagnosing sign/unit issues.

**Fixed (2026-07-24):** gravity feedforward had the wrong sign (`+g(q)` instead of `-g(q)`), causing the arm to collapse faster than free-fall at zero stiffness/damping. Verified fixed in Gazebo Harmonic (drift <0.001 rad over several seconds).

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

Features under active development — useful, but not fully polished end-to-end.

### Grasp Detection (`ur_grasp`)

Point-cloud grasp estimation from the D435. Head cam is fixed to `base_link`; use `wrist_camera:=true` for eye-in-hand (`/camera_wrist/*`).

```bash
ros2 launch ur_gazebo ur.gazebo.launch.py wrist_camera:=true
ros2 launch ur_grasp grasp_detection.launch.py colour:=red \
  camera_topic:=/camera_wrist/depth/color/points continuous_detect_hz:=0.0
ros2 service call /ur_grasp/detect std_srvs/srv/Trigger {}
```

Publishes `/ur_grasp/grasp_pose` and `/ur_grasp/grasp_marker`. Leave continuous detect off during servo approach (pose drift).

### MoveIt Task Constructor (`ur_mtc_pick_place_demo`)

**Plan + execute works** on the fallback scene (cylinder `(0.36, 0, 0.10)`). Object/table pose normally comes from the [planning scene server](#planning-scene-server-object--table-from-the-camera).

Fixed: zero-duration traj segments; phantom `mount_table` support; narrow-passage transit via FK-screened `transit_clear` + coarse OMPL + ~4 mm arm padding (2026-08-07).

Still flaky: cold-stack execute `-3` (retry); non-fallback perception scenes.

Launch: [Full MTC Pick-and-Place Demo](#full-mtc-pick-and-place-demo).

### Vision (`ur_perception`)

Color / optional YOLO detection, plus multi-view reconstruction (`object_reconstructor_node`) that fuses wrist-cam clouds via TF (+ optional ICP). Reconstruction is inspection-only — the pick pipeline does not consume it yet.

```bash
ros2 launch ur_perception perception.launch.py
ros2 topic echo /detected_objects

# Reconstruction (needs wrist_camera:=true and arm aimed at the object)
ros2 launch ur_perception reconstruct.launch.py \
  camera_topic:=/camera_wrist/depth/color/points save_path:=/tmp/object.ply
ros2 service call /ur_perception/reconstruct/start std_srvs/srv/Trigger {}
# …sweep the arm…
ros2 service call /ur_perception/reconstruct/stop std_srvs/srv/Trigger {}
```

### LLM Task Planner (`ur_llm_planner`)

Natural-language plans via local Ollama → MoveIt / gripper actions.

```bash
ollama serve && ollama pull llama3.2:3b
ros2 launch ur_llm_planner llm_planner.launch.py ollama_model:=llama3.2:3b
ros2 topic pub --once /llm_planner/command std_msgs/msg/String \
  "{data: 'pick up the red object and place it to the left of the robot'}"
```
