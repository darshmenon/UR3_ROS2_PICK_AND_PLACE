# UR3 ROS 2 Pick and Place — Concepts Guide

A deep-dive into every concept you encountered while building and debugging this project: from ROS 2 fundamentals all the way to trajectory time-parameterization bugs.

---

## Table of Contents

1. [ROS 2 Fundamentals](#1-ros-2-fundamentals)
2. [The ROS 2 Control Framework](#2-the-ros-2-control-framework)
3. [Gazebo (Ignition) Simulation](#3-gazebo-ignition-simulation)
4. [MoveIt 2 Architecture](#4-moveit-2-architecture)
5. [OMPL — Motion Planning Library](#5-ompl--motion-planning-library)
6. [Planning Pipelines & Adapters](#6-planning-pipelines--adapters)
7. [SRDF — Semantic Robot Description Format](#7-srdf--semantic-robot-description-format)
8. [Trajectory Execution & Controllers](#8-trajectory-execution--controllers)
9. [Time Parameterization (The Zero-Timestamp Bug)](#9-time-parameterization--the-zero-timestamp-bug)
10. [MoveIt Task Constructor (MTC)](#10-moveit-task-constructor-mtc)
11. [Debugging Cheat-Sheet](#11-debugging-cheat-sheet)
12. [Torque and Impedance Controllers](#12-torque-and-impedance-controllers)
13. [MoveIt Cartesian Planning (Zig-Zag Motion)](#13-moveit-cartesian-planning-zig-zag-motion)
14. [Fixed End-Effector Motion (Null-Space)](#14-fixed-end-effector-motion-null-space)
15. [Gripper Mimic Joints and Why MTC Grasping Still Works](#15-gripper-mimic-joints-and-why-mtc-grasping-still-works)
16. [Vision-Based Object Detection and 3D Pose Estimation](#16-vision-based-object-detection-and-3d-pose-estimation)
17. [LLM-Driven Task Planning with Ollama](#17-llm-driven-task-planning-with-ollama)
18. [Behavior Cloning and VLA Fine-Tuning](#18-behavior-cloning-and-vla-fine-tuning)

---

## 1. ROS 2 Fundamentals

### Nodes
A **node** is the basic computational unit in ROS 2 — a process that does one thing (read a sensor, plan a path, drive a joint). Nodes communicate through:

| Mechanism | Direction | When to use |
|-----------|-----------|-------------|
| **Topics** (pub/sub) | One-to-many | Continuous data streams (sensor readings, joint states) |
| **Services** | Request/response | Synchronous one-shot queries |
| **Actions** | Goal/feedback/result | Long-running tasks (robot motion) |
| **Parameters** | Node-specific config | Tunable values at runtime |

### Executors
An **executor** drives a node's callbacks. In this project we use a `SingleThreadedExecutor` in a background thread so the MoveIt action client can spin while `main()` blocks waiting for results:

```cpp
rclcpp::executors::SingleThreadedExecutor executor;
executor.add_node(node);
auto spinner = std::thread([&executor]() { executor.spin(); });
```

Without this spinner, the MoveIt planning/execution action calls would deadlock waiting for a response that never arrives because nothing is processing incoming messages.

### `use_sim_time`
When running in Gazebo, all nodes must set `use_sim_time: true` so they read the simulation clock rather than the wall clock. This is critical — if a controller uses wall time while move_group uses sim time, trajectory timestamps mismatch and execution fails.

---

## 2. The ROS 2 Control Framework

### Hardware Interface
`ros2_control` abstracts hardware behind a **hardware interface**. For Gazebo, the `gz_ros2_control` plugin provides a simulated hardware interface that reads/writes joint positions from the Gazebo physics engine.

```
Gazebo Physics ↔ gz_ros2_control plugin ↔ ros2_control → Controllers
```

### Controllers
Controllers read the desired state from an action server and write commands to the hardware interface:

| Controller | Purpose |
|------------|---------|
| `joint_state_broadcaster` | Publishes `/joint_states` topic from hardware readings |
| `arm_controller` (FollowJointTrajectory) | Executes a full joint trajectory on the arm |
| `gripper_controller` (GripperCommand) | Opens/closes the Robotiq gripper |

### Controller Spawning & Timing
Controllers are spawned via `controller_manager`. There's a **race condition** between Gazebo loading the robot model and the controller manager being ready. This project uses spawn delays:

```python
# ur.gazebo.launch.py
spawner(delay=35s)  # arm_controller
spawner(delay=40s)  # gripper_controller
spawner(delay=45s)  # joint_state_broadcaster
```

If you spawn too early, the controller manager hasn't loaded the robot URDF and spawn fails silently.

### `ros2_controllers.yaml`
Defines the hardware topology — which joints belong to which controller and what interface type (position/velocity/effort) they use.

---

## 3. Gazebo (Ignition) Simulation

### gz_ros2_control Plugin
Declared inside the URDF/xacro:

```xml
<plugin filename="gz_ros2_control-system" name="gz_ros2_control::GazeboSimROS2ControlPlugin">
  <parameters>$(find moveit_config)/config/ros2_controllers.yaml</parameters>
</plugin>
```

This bridges Gazebo joint physics to the `ros2_control` hardware interface.

### World File & Collision Objects
The Gazebo world defines static objects (table, cylinder, etc.) that exist in the physics simulation. For collision-aware planning, these objects must also be added to the MoveIt **Planning Scene** — they are separate representations. Gazebo knows about them physically; MoveIt needs to be told about them explicitly via `planning_scene_interface.addCollisionObjects()`.

---

## 4. MoveIt 2 Architecture

```
┌─────────────────────────────────────────────────────┐
│                    move_group node                   │
│                                                      │
│  ┌──────────────┐   ┌──────────────────────────┐    │
│  │ Planning     │   │ Trajectory Execution     │    │
│  │ Pipeline     │   │ Manager                  │    │
│  │ (OMPL/STOMP/ │   │ (sends to controllers)   │    │
│  │  PILZ/CHOMP) │   └──────────────────────────┘    │
│  └──────────────┘                                    │
│  ┌──────────────┐   ┌──────────────────────────┐    │
│  │ Planning     │   │ Controller Manager       │    │
│  │ Scene        │   │ (MoveItSimpleController  │    │
│  │ Monitor      │   │  Manager)                │    │
│  └──────────────┘   └──────────────────────────┘    │
└─────────────────────────────────────────────────────┘
         ↑ action calls           ↓ action calls
  MoveGroupInterface         arm_controller
  (your C++ node)            (ros2_control)
```

### MoveGroupInterface
Your C++ code uses `MoveGroupInterface` to talk to `move_group` over ROS 2 actions. Key calls:

```cpp
arm_group_interface.setJointValueTarget(joints);   // set goal
arm_group_interface.plan(plan);                    // ask move_group to plan
arm_group_interface.execute(plan);                 // send trajectory to controller
```

### Planning Scene
A in-memory representation of the world: the robot model + any collision objects (boxes, cylinders, meshes). The planner checks every candidate path against the planning scene to ensure it's collision-free.

### SRDF — see Section 7.

---

## 5. OMPL — Motion Planning Library

**OMPL** (Open Motion Planning Library) is a collection of sampling-based motion planning algorithms. MoveIt uses it as the default planner.

### How Sampling-Based Planning Works
1. Start from the current joint configuration
2. Randomly sample configurations in joint space
3. Test if each new configuration is collision-free
4. Connect samples into a tree/graph
5. Find a path from start to goal

Because it's random, the same query can produce different paths each run. Planning **time** directly controls how many samples are taken.

### Key Planners

| Planner | Type | Best For |
|---------|------|---------|
| **RRTConnect** | Bidirectional tree | Fast, general use ✅ |
| **RRT*** | Asymptotically optimal | Shorter paths, slower |
| **PRM** | Roadmap | Repeated queries in same environment |
| **EST** | Exploration | Narrow passages |
| **STOMP** | Stochastic gradient | Smooth, near-obstacle paths |
| **PILZ** | Deterministic | Cartesian linear/circular moves |

### Why Planning Fails
- **Timeout**: OMPL ran out of time (increase `setPlanningTime()`)
- **Start in collision**: The robot's current pose collides with something in the planning scene
- **Goal in collision**: The target joint configuration self-collides or hits scene objects
- **No valid path**: The space between start and goal is completely blocked

---

## 6. Planning Pipelines & Adapters

### Pipeline Config Files
Each planner has a YAML config that defines the plugin and adapter chain:

```
moveit_config/config/
  ompl_planning.yaml
  stomp_planning.yaml
  pilz_industrial_motion_planner_planning.yaml
```

### Request Adapters (pre-processing)
Run **before** the planner sees the request:

```yaml
request_adapters: >-
  default_planner_request_adapters/ResolveConstraintFrames
  default_planner_request_adapters/FixWorkspaceBounds
  default_planner_request_adapters/FixStartStateBounds
  default_planner_request_adapters/FixStartStateCollision
```

| Adapter | What it does |
|---------|-------------|
| `ResolveConstraintFrames` | Converts constraint frames to robot base frame |
| `FixWorkspaceBounds` | Prevents infinite workspace bounds |
| `FixStartStateBounds` | Clamps start joint values to valid limits |
| `FixStartStateCollision` | Jitters start state slightly if it's in collision |

### Response Adapters (post-processing)
Run **after** the planner returns a raw path:

```yaml
response_adapters: >-
  default_planning_response_adapters/AddTimeOptimalParameterization
  default_planning_response_adapters/ValidateSolution
  default_planning_response_adapters/DisplayMotionPath
```

| Adapter | What it does |
|---------|-------------|
| `AddTimeOptimalParameterization` | Stamps each waypoint with a time using TOTG |
| `ValidateSolution` | Double-checks the final trajectory for collisions |
| `DisplayMotionPath` | Publishes the trajectory to RViz for visualization |

### Bug 8: `planning_plugins` vs `planning_plugin`
The move_group parameter name is the **singular** `planning_plugin` (a string), not `planning_plugins` (a list). Using the wrong key silently falls back to no planner, causing all planning to fail with no useful error message.

```yaml
# Wrong:
planning_plugins: ompl_interface/OMPLPlanner

# Correct:
planning_plugin: ompl_interface/OMPLPlanner
```

### Bug: Adapter Plugin Prefix
On MoveIt 2 Humble the adapter plugin names use `Fix*` not `Check*`/`Validate*`:

```yaml
# Wrong (ROS 2 Foxy style):
default_planner_request_adapters/CheckStartStateBounds

# Correct (Humble):
default_planner_request_adapters/FixStartStateBounds
```

---

## 7. SRDF — Semantic Robot Description Format

The SRDF (`ur.srdf`) extends the URDF with higher-level semantic information MoveIt needs:

### Planning Groups
Defines named collections of joints/links that can be planned together:

```xml
<group name="arm">
  <chain base_link="torso_link" tip_link="wrist_3_link"/>
</group>
```

### Named States
Pre-defined joint configurations you can reference by name:

```xml
<group_state name="home" group="arm">
  <joint name="shoulder_pan_joint" value="0"/>
  <joint name="shoulder_lift_joint" value="-1.57"/>
  ...
</group_state>
```

### Disable Collisions
The most important section. MoveIt checks **all** link pairs for collision by default. Adjacent links (connected by a joint) obviously always touch — you must disable those checks or the robot can never move:

```xml
<disable_collisions link1="shoulder_link" link2="upper_arm_link" reason="Adjacent"/>
<disable_collisions link1="wrist_1_link"  link2="wrist_2_link"  reason="Adjacent"/>
```

**Bug fixed in this project**: A non-existent link `cylinder_1` was listed in a `disable_collisions` entry. MoveIt loads the SRDF and silently skips unknown links, but it caused confusing log warnings. Removed it.

---

## 8. Trajectory Execution & Controllers

### FollowJointTrajectory Action
The standard ROS interface for arm motion. Your trajectory must contain:
- Joint names (in the same order as the controller config)
- A list of `JointTrajectoryPoint`s, each with:
  - `positions` (radians)
  - `velocities`
  - `accelerations`
  - **`time_from_start`** ← this must be strictly increasing!

### `moveit_controllers.yaml`
Maps MoveIt's abstract controller names to the actual ROS 2 action servers:

```yaml
moveit_simple_controller_manager:
  arm_controller:
    type: FollowJointTrajectory
    joints: [shoulder_pan_joint, ..., wrist_3_joint]
    action_ns: follow_joint_trajectory
```

### Allowed Start Tolerance
```yaml
trajectory_execution:
  allowed_start_tolerance: 0.1   # radians
```
If the robot's current joint positions differ from the trajectory's first point by more than this tolerance, execution is rejected. Set it higher if controllers drift.

---

## 9. Time Parameterization — The Zero-Timestamp Bug

This was the final execution bug in this project. Understanding it fully:

### Root Cause
OMPL's raw output is a **geometric path** — a sequence of joint configurations with **no time information**. Before the trajectory can be sent to a controller it must be **time-parameterized**: each waypoint needs a `time_from_start` value.

MoveIt is supposed to do this automatically via the `AddTimeOptimalParameterization` response adapter. But if the response adapter plugin fails to load (missing library, wrong plugin name format, Humble-specific quirks), all timestamps stay at `0.0`.

### The Error
```
[arm_controller]: Time between points 0 and 1 is not strictly increasing,
                  it is 0.000000 and 0.000000 respectively
```
The `ros2_control` FollowJointTrajectory controller validates that timestamps strictly increase before accepting a goal. All-zero timestamps → immediate rejection → execution fails.

### The Fix (Applied in this project)
Instead of relying on the response adapter, we apply **Time Optimal Trajectory Generation (TOTG)** explicitly in C++ immediately after `plan()` succeeds:

```cpp
#include <moveit/robot_trajectory/robot_trajectory.h>
#include <moveit/trajectory_processing/time_optimal_trajectory_generation.h>

// After plan() succeeds:
trajectory_processing::TimeOptimalTrajectoryGeneration totg;

auto robot_traj = std::make_shared<robot_trajectory::RobotTrajectory>(
    arm_group_interface.getRobotModel(), "arm");

robot_traj->setRobotTrajectoryMsg(
    *arm_group_interface.getCurrentState(),
    plan.trajectory_);

totg.computeTimeStamps(*robot_traj, vel_scale, acc_scale);

// Write stamped trajectory back into the plan
robot_traj->getRobotTrajectoryMsg(plan.trajectory_);

// Now safe to execute
arm_group_interface.execute(plan);
```

### TOTG Algorithm
TOTG (Time Optimal Trajectory Generation) treats the path as a 1D problem along path-length and finds the fastest feasible timing that respects per-joint velocity and acceleration limits. It's deterministic and extremely fast (microseconds).

### Why Velocity/Acceleration Scaling Matters
```cpp
arm_group_interface.setMaxVelocityScalingFactor(0.3);     // 30% of joint limits
arm_group_interface.setMaxAccelerationScalingFactor(0.3);  // 30% of joint limits
```
At 100% scaling on a simulated robot, the trajectory completes near-instantly in physics time, making it hard for Gazebo to track. 30% gives the controller room to actually follow the trajectory.

---

## 10. MoveIt Task Constructor (MTC)

MTC is a higher-level framework built on top of MoveIt for **task planning** — sequences of motion stages like pick-and-place.

### Core Concepts

```
Task
├── Stage: CurrentState        ← where the robot is now
├── Stage: MoveTo (pre-grasp)  ← move arm above object
├── Stage: Grasp               ← close gripper (sub-task)
│   ├── Stage: Approach
│   ├── Stage: GraspPose
│   └── Stage: Close Gripper
├── Stage: Lift                ← move up with object
├── Stage: MoveTo (place pose) ← move to drop location
└── Stage: Place               ← open gripper + retreat
```

### Stage Types
| Type | Description |
|------|-------------|
| `CurrentState` | Reads current robot state |
| `MoveTo` | Plans to a named target or joint config |
| `MoveRelative` | Plans a relative Cartesian move |
| `Connect` | Bridges two adjacent stages (runs a planner) |
| `GenerateGraspPose` | Samples grasp poses around an object |
| `SimpleGrasp` | Composite: approach + IK + close |

### MTC vs Direct MoveIt
| | Direct MoveIt | MTC |
|--|---|---|
| Use for | Single motions | Multi-step tasks |
| Backtracking | Manual | Automatic |
| Grasp pose generation | Manual | Built-in |
| Pick-and-place | ~200 lines | ~80 lines |

---

## 11. Debugging Cheat-Sheet

### Find why planning failed
```bash
# Check move_group log
cat ~/.ros/log/latest/move_group*.log | grep -E "OMPL|plan|abort|error" -i

# Check if planner plugin loaded
grep "planning_plugin\|OMPLPlanner" ~/.ros/log/latest/move_group*.log
```

### Find why execution failed
```bash
# Look for controller rejection reason
grep -E "reject|abort|tolerance|timestamp|strictly" /tmp/gazebo.log
```

### Common errors and fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `Planning request aborted` after 2s | Timeout | Increase `setPlanningTime()` |
| `Time between points not strictly increasing` | Zero timestamps | Apply TOTG explicitly (see §9) |
| `Goal was rejected by server` | Controller validation failed | Check timestamps + joint order |
| `allowed_start_tolerance exceeded` | Start state mismatch | Increase `allowed_start_tolerance` |
| No planner loaded | `planning_plugins` vs `planning_plugin` typo | Use singular `planning_plugin` |
| `cylinder_1` link warnings | Non-existent link in SRDF | Remove from `disable_collisions` |
| Controllers not spawning | Spawn delay too short | Increase delay in launch file |

### Verify joint states are publishing
```bash
ros2 topic echo /joint_states --once
```

### Check what controllers are running
```bash
ros2 control list_controllers
```

### Inspect the planned trajectory
```bash
ros2 topic echo /display_planned_path --once
```

---

*This document covers every concept encountered debugging the UR3 ROS 2 pick-and-place project. For the official references see the [MoveIt 2 docs](https://moveit.picknik.ai/) and [ros2_control docs](https://control.ros.org/).*

## 12. Torque and Impedance Controllers

In the `ros2_control` ecosystem, you can extend the robot's capabilities by adding specialized controllers beyond pure position control:

### Torque Control (`forward_command_controller/ForwardCommandController`)
A torque controller lets you bypass trajectory planning and send raw effort (torque) values directly to the joints. In ROS 2 Humble:
- You use `forward_command_controller/ForwardCommandController` and configure it to use the `effort` interface.
- It requires the hardware interface to support `effort` command interfaces.

### Impedance Control
Impedance controllers treat the robot like a mass-spring-damper system, allowing it to act compliantly when it hits obstacles rather than rigidly tracking a position and commanding infinite torque. 
- While native impedance controllers often require custom C++ plugins, a baseline can be established using a `joint_trajectory_controller` mapped to `effort` command interfaces. MoveIt can then plan trajectories that are executed compliantly.

## 13. MoveIt Cartesian Planning (Zig-Zag Motion)
To move the end-effector through precise waypoints (like a zig-zag), we rely on MoveIt's Cartesian planning capabilities:
- **`computeCartesianPath`**: Takes a vector of `geometry_msgs::msg::Pose` waypoints. It interpolates linearly between them in Cartesian space and uses Inverse Kinematics (IK) to calculate the corresponding joint positions.
- **Orientation**: It's crucial to set the correct quaternion orientation for the end-effector (e.g., `x=1.0, w=0.0` for pointing straight down) in every waypoint to prevent the arm from twisting wildly between points.

## 12. Torque and Impedance Controllers

In the `ros2_control` ecosystem, you can extend the robot capability by adding specialized controllers beyond pure position control:

### Torque Control (`forward_command_controller/ForwardCommandController`)
A torque controller lets you bypass trajectory planning and send raw effort (torque) values directly to the joints. In ROS 2 Humble:
- You use `forward_command_controller/ForwardCommandController` and configure it to use the `effort` interface.
- It requires the hardware interface to support `effort` command interfaces.

### Impedance Control
Impedance controllers treat the robot like a mass-spring-damper system, allowing it to act compliantly when it hits obstacles rather than rigidly tracking a position and commanding infinite torque. 
- While native impedance controllers often require custom C++ plugins, a baseline can be established using a `joint_trajectory_controller` mapped to `effort` command interfaces. MoveIt can then plan trajectories that are executed compliantly.

## 13. MoveIt Cartesian Planning (Zig-Zag Motion)
To move the end-effector through precise waypoints (like a zig-zag), we rely on MoveIt Cartesian planning capabilities via Inverse Kinematics (IK):
- **Pilz Industrial Motion Planner**: We use the PILZ `LIN` (Linear) trajectory planner to draw strictly straight Cartesian lines between points. Unlike regular joint-space planners (which move joints from A to B in the most efficient joint configuration, resulting in curved end-effector paths), `LIN` forces the end-effector to travel in a straight line in 3D space.
- **Starting Points (`PTP` vs `LIN`)**: Because a `LIN` motion requires a pre-existing Cartesian context (i.e., you can only draw a line if your start and end point are in the same general pose family), we must use a Point-to-Point (`PTP`) planner (like OMPL or Pilz `PTP`) to move to the very first point of our shape via standard joint-space planning. 
- **Time Parameterization**: Planners generate a geometrical path (points in space) but often fail to add velocity/acceleration timestamps to the trajectory constraints. Without explicit Time Optimal Trajectory Generation (TOTG) applied to the trajectory, the `ros2_control` execution manager will instantly reject the plan.
- **Simulation Delay**: When running Gazebo Harmonic simulations, physics and the `ros2_control` ecosystem need substantial time to initialize. For this project, a 60-second delay is strictly necessary before running custom MoveIt C++ nodes to ensure the `arm_controller` and clock synchronizer are fully spawned. Otherwise, controllers will time out waiting for the `joint_states` topic or action servers.

## 15. Gripper Mimic Joints and Why MTC Grasping Still Works

### What Mimic Joints Are

The Robotiq 2F-85 gripper has **one actuated joint** (`finger_joint`) controlled by `gripper_controller`, and **five passive joints** that should mirror it mechanically:

| Joint | Multiplier | Range |
|---|---|---|
| `left_inner_knuckle_joint` | +1 | 0 → 0.8757 |
| `left_inner_finger_joint` | -1 | 0 → -0.8757 |
| `right_outer_knuckle_joint` | ±1 | 0 → 0.81 |
| `right_inner_knuckle_joint` | +1 | 0 → 0.8757 |
| `right_inner_finger_joint` | -1 | 0 → -0.8757 |

The URDF `<mimic>` tag encodes this relationship:

```xml
<joint name="left_inner_knuckle_joint" type="revolute">
  ...
  <mimic joint="finger_joint" multiplier="1" offset="0"/>
</joint>
```

### Who Reads Mimic Tags

| Component | Reads `<mimic>`? | Effect |
|---|---|---|
| **`robot_state_publisher`** | **Yes** | Derives mimic joint TF transforms from `finger_joint` state → RViz shows correct visual |
| **MoveIt planning** | **Yes** | Includes mimic joints in collision geometry when planning gripper poses |
| **Ignition Gazebo physics** | **Yes** | Mimic constraints applied via URDF→SDF conversion on spawn |

When the robot is spawned into Ignition Gz from `/robot_description` (via `ros_gz_sim`), the URDF-to-SDF converter translates `<mimic>` tags into native Ignition physics joint constraints. The old Gazebo Classic plugins (`libgazebo_mimic_joint_plugin.so`, `libroboticsgroup_gazebo_mimic_joint_plugin.so`) still present in the URDF are dead code — they never load in Ignition — but they are also not needed since Ignition handles it natively.

### Why MTC Pick-and-Place Works

MTC's `Pick` stage combines **real physics gripper closure** with a **software attachment**:

```
1. Plan + execute: finger_joint → closed   (GripperCommand action)
   → mimic joints physically follow in Gazebo (fingers actually close)
2. attachObject("object", "tool0")         ← planning scene weld
   → object rigidly attached to end-effector for collision-aware planning
3. Plan + execute: lift arm               (object follows in both Gazebo and MoveIt)
```

`attachObject()` is still the key step for **planning** — it tells MoveIt's collision checker to treat the object as part of the robot so the planner avoids collisions with it during lifting. Without it, MoveIt would try to plan around the object even while carrying it.

### Practical Implications

- **RViz visualization**: Correct — `robot_state_publisher` derives mimic positions from `finger_joint` state.
- **MoveIt collision checking**: Correct — planner sees gripper in actual planned pose.
- **Gazebo physics contact**: Works — mimic joints follow `finger_joint` via URDF→SDF spawn conversion.
- **MTC grasping**: Works via both physical closure + `attachObject()` for planning.
- **Old Gazebo Classic plugins in URDF**: Dead code, harmless, never load in Ignition.

---

## 14. Fixed End-Effector Motion (Null-Space)
Moving other joints while strictly keeping the end-effector stationary requires the robot to be **kinematically redundant**.
- The UR3 is a **6-DOF (Degrees of Freedom)** arm. To fix the 6 aspects of the end-effector pose (X, Y, Z, Roll, Pitch, Yaw), all 6 joints are mathematically constrained.
- Unless the arm is in a singularity, there is no "null-space" in a 6-DOF arm to move the elbow while keeping the gripper perfectly still.
- A **7-DOF** arm (like the Franka Emika Panda) has an extra degree of freedom, allowing for null-space motions where the elbow can move while the end-effector pose is completely constrained.

---

## 16. Vision-Based Object Detection and 3D Pose Estimation

### Color-Based Detection (HSV)
The `ur_perception` package uses OpenCV HSV thresholding as the primary detection method. Why HSV instead of RGB?

- **RGB** mixes color and brightness — the same "red" object looks completely different under bright vs dim lighting.
- **HSV** (Hue, Saturation, Value) separates color (hue) from lighting (value). You can threshold hue ± a margin and ignore brightness variation.
- Red wraps around the hue circle (0° and 360° are both red), so two separate threshold ranges are needed and OR'd together.

The detection pipeline: BGR → HSV → threshold mask → morphological opening (remove noise) → close (fill holes) → find contours → fit bounding boxes.

### Back-Projection to 3D
A depth camera gives a 2D pixel `(u, v)` plus a depth value `d`. The 3D point in camera space is:

```
X = (u - cx) * d / fx
Y = (v - cy) * d / fy
Z = d
```

Where `fx, fy, cx, cy` are the camera intrinsics from the `CameraInfo` topic. A single pixel's depth is noisy, so we sample a 5×5 patch around the centroid and take the median — much more robust than a single measurement.

### TF2 Transform to Robot Frame
The camera is mounted off the robot (`camera_head_link`). The detected 3D point is in camera frame. To plan around it, MoveIt needs the position in `base_link` frame. TF2 tracks the transform chain `base_link → ... → camera_head_link` (published by `robot_state_publisher`) and lets you transform any stamped pose between frames in one call.

### Publishing to MoveIt Planning Scene
Detected objects are added to the MoveIt planning scene as `CollisionObject` with a CYLINDER primitive. This means:
1. MoveIt path planning automatically avoids them
2. MTC's `GenerateGraspPose` stage finds valid grasps around them
3. When you pick an object, `attachObject()` welds it to the gripper in the scene

The key detail: publish with `PlanningScene.is_diff = True` so MoveIt **merges** your objects with the existing scene instead of replacing it.

---

## 17. LLM-Driven Task Planning with Ollama

### Why Use an LLM for Task Planning?
Classical pick-and-place pipelines hardcode the task sequence. An LLM planner lets you say *"sort the blocks by color"* and have the robot figure out which blocks to pick, in what order, and where to put them — adapting to whatever objects the perception pipeline currently sees. In this project, we use **Ollama** to run models locally (like Llama 3.2 or Mistral) without needing a cloud API key.

### The Pipeline
```
User command (string)
  → Ollama LLM (running locally with scene context as JSON)
  → Structured task list (JSON)
  → MotionExecutor (ROS 2 action clients)
  → Robot motion
```

Ollama receives:
- The natural language command
- A JSON list of currently detected objects with their 3D positions
- The list of available named poses and action types

Ollama returns:
```json
{
  "explanation": "I will pick the red block at (0.30, 0.05) and place it in the left bin",
  "tasks": [
    {"action": "move_to_named_pose", "pose_name": "ready"},
    {"action": "pick", "object_id": "red_0", "object_x": 0.30, "object_y": 0.05, "object_z": 0.04},
    {"action": "place", "x": -0.15, "y": 0.25, "z": 0.10}
  ]
}
```

### Why Named Poses Need Explicit Joint Values
MoveIt's C++ `MoveGroupInterface::setNamedTarget("home")` looks up joint values from the SRDF and sends them as `JointConstraint` objects in the action goal. The action server itself does NOT do this lookup — it only receives constraints. So Python code calling the action directly must embed the actual joint values. These are hardcoded from the SRDF in `motion_executor.py`.

### Avoiding Deadlock in ROS 2 Callbacks
`rclpy.spin_until_future_complete(node, future)` must not be called from inside a `rclpy.spin()` callback — the executor is already spinning and re-entering it causes a deadlock. The solution: when a command arrives on the subscription callback, spawn a `threading.Thread` to run the planning + execution. The main spin loop stays unblocked while the thread waits for action results.

---

## 18. Behavior Cloning and VLA Fine-Tuning

### What is Behavior Cloning?
Behavior Cloning (BC) is the simplest form of imitation learning: record expert demonstrations (state → action pairs), then train a neural network to predict the action from the state using supervised learning (MSE loss). No reward function needed.

**State**: joint positions (6 arm joints) + gripper position + camera RGB image
**Action**: next joint positions (same format) — BC treats manipulation as a regression problem

### Data Collection
`ur_data_collector/collector_node.py` records:
- Joint states at ~5 Hz (synchronized with camera)
- RGB image (424×240)
- Depth image
- Saves to HDF5 format (efficient random access, no ROS bag overhead)

### BC Policy Architecture
The `train_bc.py` script trains a small CNN + MLP policy:
```
RGB image (3×240×424)
  → 3 conv layers (ReLU + MaxPool)
  → flatten → 512-dim features
  → concat with joint positions (6)
  → MLP (256 → 256 → 7 outputs)
  → predicted next joint positions
```

### Path to VLA Fine-Tuning
A **Vision-Language-Action (VLA)** model (e.g., OpenVLA, RT-2) extends BC with a language conditioning: `(image, text_command) → action`. Fine-tuning one requires:

1. Generate a dataset of `(image, language_annotation, action)` tuples from your Gazebo demos
2. Convert to the HuggingFace Datasets format expected by the VLA trainer
3. Fine-tune on a GPU (≥24GB VRAM for quantized fine-tuning)
4. Deploy the inference node in ROS 2 — subscribe to camera + command topic, publish joint targets

The `ur_data_collector` HDF5 format is designed to be easy to convert to these training formats. Each episode is a contiguous chunk of `(rgb_images, joint_positions, actions)` arrays.
