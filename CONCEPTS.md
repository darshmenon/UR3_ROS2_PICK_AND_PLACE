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
9. [Time Parameterization — TOTG Failure and the IPTP + Pilz Fix](#9-time-parameterization--totg-failure-and-the-iptp--pilz-fix)
10. [MoveIt Task Constructor (MTC)](#10-moveit-task-constructor-mtc)
11. [Debugging Cheat-Sheet](#11-debugging-cheat-sheet)
12. [Torque and Impedance Controllers](#12-torque-and-impedance-controllers)
13. [MoveIt Cartesian Planning (Zig-Zag Motion)](#13-moveit-cartesian-planning-zig-zag-motion)
14. [Fixed End-Effector Motion (Null-Space)](#14-fixed-end-effector-motion-null-space)
15. [Gripper Mimic Joints and Why MTC Grasping Still Works](#15-gripper-mimic-joints-and-why-mtc-grasping-still-works)
16. [Vision-Based Object Detection and 3D Pose Estimation](#16-vision-based-object-detection-and-3d-pose-estimation)
17. [LLM-Driven Task Planning with Ollama](#17-llm-driven-task-planning-with-ollama)
18. [Behavior Cloning and VLA Fine-Tuning](#18-behavior-cloning-and-vla-fine-tuning)
19. [IK Service — Cartesian Poses to Joint Values](#19-ik-service--cartesian-poses-to-joint-values)
20. [Pilz Industrial Motion Planner — PTP vs LIN](#20-pilz-industrial-motion-planner--ptp-vs-lin)
21. [SRDF Collision Matrix — Gripper Self-Collision Entries](#21-srdf-collision-matrix--gripper-self-collision-entries)
22. [Gripper Stall Detection — ABORTED Means Success](#22-gripper-stall-detection--aborted-means-success)
23. [Headless Testing and RViz Crashes](#23-headless-testing-and-rviz-crashes)
24. [Point Cloud TF Frames and ROS 2 QoS](#24-point-cloud-tf-frames-and-ros-2-qos)
25. [PCL Plane and Object Segmentation](#25-pcl-plane-and-object-segmentation)
26. [Grasp Detection — ur_grasp Package](#26-grasp-detection--ur_grasp-package)
27. [Data Collection for Behavior Cloning — ur_data_collector](#27-data-collection-for-behavior-cloning--ur_data_collector)
28. [Sequential Pick-and-Place with Python MoveIt Client](#28-sequential-pick-and-place-with-python-moveit-client)
29. [MTC Humble vs Jazzy Compatibility](#29-mtc-humble-vs-jazzy-compatibility)

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
| `AddTimeParameterization` | Stamps each waypoint with a time using IPTP (Iterative Parabolic) |
| `ValidateSolution` | Double-checks the final trajectory for collisions |
| `DisplayMotionPath` | Publishes the trajectory to RViz for visualization |

> **Note**: The adapter was originally `AddTimeOptimalParameterization` (TOTG). It was replaced with `AddTimeParameterization` (IPTP) because TOTG silently produces all-zero timestamps in MoveIt 2 Humble when the path has near-duplicate waypoints or missing joint limits. See §9.

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

## 9. Time Parameterization — TOTG Failure and the IPTP + Pilz Fix

### The Problem: Zero Timestamps

OMPL's raw output is a **geometric path** — joint configurations with **no time information**. Before a trajectory reaches a `ros2_control` controller it must be **time-parameterized**: each waypoint needs a `time_from_start`.

MoveIt's response adapter chain is supposed to do this automatically. In Humble, the original adapter was `AddTimeOptimalParameterization` (TOTG). It silently produces all-zero timestamps in two cases:

1. **Near-duplicate waypoints** — TOTG's underlying algorithm returns failure without logging anything at the default log level.
2. **Missing joint limits** — TOTG reads velocity/acceleration limits from the RobotModel. If any joint has zero limits, TOTG silently fails. IPTP handles this more gracefully.

When timestamps are all zero the controller rejects the goal immediately:

```
[arm_controller]: Time between points 0 and 1 is not strictly increasing,
                  it is 0.000000 and 0.000000 respectively
CONTROL_FAILED (-4)
```

### Fix Part 1: Switch OMPL Pipeline to IPTP

Replace `AddTimeOptimalParameterization` with `AddTimeParameterization` (IPTP — Iterative Parabolic Time Parameterization) in `ompl_planning.yaml`:

```yaml
response_adapters: >-
  default_planning_response_adapters/AddTimeParameterization
  default_planning_response_adapters/ValidateSolution
  default_planning_response_adapters/DisplayMotionPath
```

IPTP uses trapezoidal velocity profiles rather than time-optimal bang-bang arcs. It's less optimal but never silently fails — it always produces non-zero timestamps as long as there are at least 2 distinct waypoints.

### Fix Part 2: Use Pilz PTP for All Moves (Bypasses the Problem Entirely)

For this project, **all arm motions now go through the Pilz Industrial Motion Planner with `PTP` (Point-to-Point)** rather than OMPL. Pilz generates its own timestamps internally — it never calls TOTG or IPTP at all, so the zero-timestamp problem cannot occur.

```python
req.pipeline_id = "pilz_industrial_motion_planner"
req.planner_id = "PTP"
req.max_velocity_scaling_factor = 0.3
req.max_acceleration_scaling_factor = 0.3
```

Pilz PTP computes a straight-line motion in **joint space** with a trapezoidal velocity profile. It's deterministic, fast, and reliable.

### Comparison: OMPL vs Pilz vs Cartesian

| Method | Path Type | Time Stamping | Use When |
|--------|-----------|---------------|----------|
| OMPL + IPTP | Joint-space, sampled | IPTP (trapezoidal) | Obstacle avoidance needed |
| Pilz PTP | Joint-space, straight-line | Built-in trapezoidal | Fast, reliable joint moves |
| Pilz LIN | Cartesian straight-line | Built-in trapezoidal | End-effector must travel in a straight line |
| IK + Pilz PTP | Joint-space to IK solution | Built-in trapezoidal | Cartesian target, no LIN needed |

### Why Velocity/Acceleration Scaling Matters
```python
req.max_velocity_scaling_factor = 0.3      # 30% of joint limits
req.max_acceleration_scaling_factor = 0.3  # 30% of joint limits
```
At 100% scaling, the trajectory completes near-instantly in physics time. Gazebo's controller can't track it and the action returns `ABORTED`. 30% gives the controller enough time to follow.

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

## 19. IK Service — Cartesian Poses to Joint Values

### Why Not `computeCartesianPath`?

MoveIt's `computeCartesianPath` generates a dense set of waypoints along a straight Cartesian line. After planning, those waypoints still need time-stamping via a response adapter (TOTG/IPTP). In Humble this chain is unreliable for short or trivial paths.

A cleaner approach: use the **IK service** to convert a single Cartesian pose directly into joint values, then plan a Pilz PTP motion to those joint values. This sidesteps the adapter chain entirely.

### The `/compute_ik` Service

MoveIt exposes `moveit_msgs/srv/GetPositionIK` at `/compute_ik`:

```python
from moveit_msgs.srv import GetPositionIK

req = GetPositionIK.Request()
req.ik_request.group_name = "arm"
req.ik_request.pose_stamped = target_pose      # PoseStamped in base_link frame
req.ik_request.avoid_collisions = True
req.ik_request.timeout.sec = 5

# Optionally seed with current joint state for nearest solution:
req.ik_request.robot_state.joint_state = current_joint_state
```

### Seeding the IK Solver

KDL (the IK solver used here) is a **local** solver — it walks from the seed configuration toward the solution. Without a good seed, it can return a valid but highly-wrapped solution (e.g., `shoulder_lift = -6.03 rad` instead of `-1.57 rad`). Such solutions make Pilz PTP plan a huge joint-space motion even though the end-effector barely moves.

The fix: seed the IK request with the current joint state **and** override `shoulder_pan` to point roughly at the target:

```python
seed.shoulder_pan_joint = math.atan2(target_y, target_x)
```

This steers KDL toward the most natural arm configuration.

### Normalizing Wrist Joints

After IK returns a solution, wrist joints (`wrist_1`, `wrist_2`, `wrist_3`) may be ±2π away from the nearest equivalent angle. Normalize them to `[-π, π]` before sending to Pilz PTP to prevent unnecessary full rotations:

```python
import math
value = ((value + math.pi) % (2 * math.pi)) - math.pi
```

---

## 20. Pilz Industrial Motion Planner — PTP vs LIN

### What Pilz Is

Pilz is a **deterministic** motion planner (unlike OMPL which is sampling-based). It ships with MoveIt 2 and provides two key trajectory types:

| Type | Motion | When to Use |
|------|--------|-------------|
| **PTP** | Straight-line in joint space | Going to a named pose or IK solution |
| **LIN** | Straight-line in Cartesian space | Precise Cartesian approach/retract |
| **CIRC** | Circular arc in Cartesian space | Arcs and circles |

### Why We Use PTP for Everything

Pilz LIN requires that the entire path between start and goal be reachable in Cartesian space (no singularities, no joint limit violations along the line). For the UR3, LIN from a home-like configuration to a pre-grasp pose often violates elbow joint velocity limits (`elbow_joint velocity 13.96 > limit 3.14`).

PTP makes no Cartesian guarantees — it just moves each joint from A to B in a synchronized trapezoidal profile. This is almost always feasible as long as the goal configuration itself is valid.

### Pilz Self-Collision Checking

Unlike OMPL (which can sometimes miss self-collisions due to sparse sampling), Pilz checks the **entire straight-line path** in joint space for collisions. This means you get `INVALID_MOTION_PLAN (-2)` if any point along the straight joint-space path is in self-collision.

This is why we need comprehensive `<disable_collisions>` entries in the SRDF for arm links vs gripper links — the gripper geometry is always "nearby" the wrist, and Pilz will flag false collisions if those pairs aren't disabled.

---

## 21. SRDF Collision Matrix — Gripper Self-Collision Entries

### The Problem

When the gripper is mounted on the wrist, many arm links are geometrically close to gripper links. MoveIt's collision checker considers all non-adjacent link pairs by default. This causes `INVALID_MOTION_PLAN` errors because Pilz detects apparent self-collision on the planned path.

### Required Disable Entries

Every arm link that is geometrically near the gripper needs a `<disable_collisions>` entry with every gripper link:

```xml
<!-- Each of these arm links needs entries for ALL 11 gripper links -->
<!-- Gripper links: robotiq_arg2f_base_link, left/right outer_knuckle,
     left/right outer_finger, left/right inner_knuckle,
     left/right inner_finger, left/right inner_finger_pad -->

<disable_collisions link1="forearm_link"   link2="left_inner_finger"  reason="Never"/>
<disable_collisions link1="upper_arm_link" link2="right_inner_knuckle" reason="Never"/>
<!-- ... etc for all combinations -->
```

**Arm links that need gripper entries**: `base_link`, `shoulder_link`, `upper_arm_link`, `forearm_link`, `wrist_1_link`, `wrist_2_link`, `wrist_3_link`.

### Debugging Self-Collision Errors

When Pilz returns `INVALID_MOTION_PLAN (-2)`, it's almost always a missing disable entry. To find which pair:

```bash
# Enable collision debug logging in move_group:
ros2 run moveit_ros_move_group move_group \
  --ros-args --log-level collision_detection:=debug
```

Or check the Allowed Collision Matrix from a running system:

```python
from moveit_msgs.srv import GetPlanningScene
from moveit_msgs.msg import PlanningSceneComponents
# request ACM, then inspect entry_names / entry_values
```

---

## 22. Gripper Stall Detection — ABORTED Means Success

### GripperActionController Behavior

The `position_controllers/GripperActionController` sends a `GripperCommand` goal with a target position and max effort. When the gripper is closing on an object:

1. The finger tries to reach `position = 0.8` (fully closed)
2. The object blocks the finger before it reaches 0.8
3. The joint velocity drops to zero while position error remains
4. The controller interprets this as a **stall** and returns `ABORT`

```
[gripper_controller]: Goal was aborted because the gripper stalled
```

**This is normal and expected behavior when grasping an object.** The gripper did close — it just stopped at the object's surface instead of the commanded position.

### Handling It in Code

Treat any non-`TIMED_OUT` result from the gripper action as success:

```python
status = result_handle.status
if status == GoalStatus.STATUS_SUCCEEDED or status == GoalStatus.STATUS_ABORTED:
    return True   # ABORTED = stalled on object = successful grasp
return status != GoalStatus.STATUS_EXECUTING  # timeout = real failure
```

### Stall vs Failure

| Outcome | Status | Meaning |
|---------|--------|---------|
| Gripper reached target | `SUCCEEDED` | No object, or very thin object |
| Gripper stalled | `ABORTED` | Object grasped — this is the normal pick result |
| Gripper timed out | `TIMED_OUT` | Real failure (controller not responding) |

---

## 23. Headless Testing and RViz Crashes

### RViz SIGSEGV in Humble

RViz2 with the MoveIt MotionPlanning plugin crashes (exit code -11, SIGSEGV) in MoveIt 2 Humble if `planning_pipelines` configuration is not passed to the RViz node. The fix:

```python
rviz_node = Node(
    package="rviz2", executable="rviz2",
    parameters=[
        moveit_config.robot_description,
        moveit_config.robot_description_semantic,
        moveit_config.robot_description_kinematics,
        moveit_config.planning_pipelines,   # ← required, prevents SIGSEGV
        {"use_sim_time": True}
    ],
)
```

### Running Headlessly

Add a `use_rviz` launch argument to skip RViz entirely during testing:

```python
DeclareLaunchArgument("use_rviz", default_value="true"),

Node(..., condition=IfCondition(LaunchConfiguration("use_rviz")))
```

Then launch with:

```bash
ros2 launch ur_gazebo ur.gazebo.launch.py use_rviz:=false
```

This is important for running in environments without a display, and makes startup faster (RViz adds ~5s to startup time).

### TF Time Jump After Process Restart

When `move_group` is killed and restarted, the TF buffer sometimes detects a time jump:

```
Detected jump back in time. Clearing TF buffer.
```

If a test runs immediately after this, MoveIt trajectory execution fails with `TIMED_OUT` because TF transforms are unavailable for several seconds after the buffer clears. Wait ~10 seconds after any `move_group` restart before running tests.

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

---

## 24. Point Cloud TF Frames and ROS 2 QoS

### Optical Frame vs Link Frame

Depth cameras publish point clouds in the **optical frame** convention (Z-forward, X-right, Y-down per REP-103), not the link frame (X-forward, Z-up). A common mistake is setting `<gz_frame_id>` to the link frame — this makes the cloud appear rotated 90° in RViz.

**Fix**: Set `<gz_frame_id>camera_head_depth_optical_frame</gz_frame_id>` so the bridge stamps messages with the correct optical frame ID.

### Verifying TF

```bash
ros2 run tf2_ros tf2_echo base_link camera_head_depth_optical_frame
# Expect non-identity translation + rotation including -π/2 roll and -π/2 yaw (optical rotation)

ros2 run tf2_tools view_frames  # dump full TF tree to PDF
```

### ROS 2 QoS Mismatch

Ignition Gazebo's `ros_gz_bridge` publishes sensor data with `BEST_EFFORT` reliability. If your subscriber uses the default `RELIABLE` QoS, it will **never receive any messages** — no error is logged, messages are silently dropped.

```cpp
// Wrong — default QoS is RELIABLE:
this->create_subscription<sensor_msgs::msg::PointCloud2>(topic, 10, callback);

// Correct — match Gazebo's BEST_EFFORT:
auto qos = rclcpp::QoS(rclcpp::KeepLast(10)).best_effort();
this->create_subscription<sensor_msgs::msg::PointCloud2>(topic, qos, callback);
```

This affects **any** node subscribing to Gazebo sensor topics: point clouds, images, laser scans.

### Lazy Bridge

The `ros_gz_bridge` for point clouds is **lazy** by default — it only starts bridging when a ROS 2 subscriber connects. If you check `ros2 topic hz` before any subscriber exists, the topic will show 0 Hz even though the Gazebo sensor is publishing.

### Octomap (Green Dots in Planning Scene)

MoveIt's `PointCloudOctomapUpdater` converts the live point cloud into a voxel occupancy map (octomap) that move_group uses for collision avoidance. To enable it:

1. Install: `sudo apt install ros-humble-moveit-ros-perception`
2. Configure `sensors_3d.yaml`:
```yaml
sensors:
  - default_sensor
default_sensor:
  sensor_plugin: occupancy_map_monitor/PointCloudOctomapUpdater
  point_cloud_topic: /camera_head/depth/color/points
  max_range: 1.5
  max_update_rate: 1.0
  padding_offset: 0.2
```
3. The green/grey voxels visible in RViz's PlanningScene display are the octomap.

---

## 25. PCL Plane and Object Segmentation

### Pipeline

The `get_planning_scene_server` uses PCL to detect objects on a table:

```
Raw PointCloud2
  → transform to base_link
  → CropBox (workspace limits)
  → RANSAC plane segmentation → table plane + above-table cloud
  → EuclideanClusterExtraction → individual object clusters
  → cylinder/box fitting per cluster → CollisionObject
```

### RANSAC Plane Segmentation

```cpp
pcl::SACSegmentation<PointT> seg;
seg.setModelType(pcl::SACMODEL_PLANE);
seg.setMethodType(pcl::SAC_RANSAC);
seg.setDistanceThreshold(0.01);  // 1 cm inlier tolerance
seg.setMaxIterations(1000);
```

The table plane must have enough inliers — if the crop box cuts the table in half, RANSAC may fail to converge. **Always crop symmetrically around the workspace center** (include both ±Y).

### Cluster Extraction

```cpp
pcl::EuclideanClusterExtraction<PointT> ec;
ec.setClusterTolerance(0.02);   // 2 cm gap = different cluster
ec.setMinClusterSize(150);       // filter noise
ec.setMaxClusterSize(1000000);
```

If `min_cluster_size` is too large, small objects (narrow cylinders) get filtered. Reduce to 50–100 for thin objects.

### Cylinder Fitting

```cpp
seg.setModelType(pcl::SACMODEL_CYLINDER);
seg.setNormalDistanceWeight(0.1);
seg.setRadiusLimits(0.01, 0.05);  // 1–5 cm radius
seg.setDistanceThreshold(0.02);
```

Returns 7 coefficients: `[point_on_axis.x, y, z, axis.x, y, z, radius]`. The cylinder axis direction gives the object's orientation; the midpoint along the axis at half-height gives the grasp center.

### Debug PCD Files

The server saves intermediate clouds to `/tmp/` at each pipeline step:
- `4_convertToPCL_debug_cloud.pcd` — full transformed cloud
- `5_support_plane_debug_cloud.pcd` — table inliers
- `5_objects_cloud_debug_cloud.pcd` — everything above the table

View them with: `ros2 run rviz2 rviz2` and add a PointCloud2 display pointed at a file, or use `pcl_viewer` from `ros-humble-pcl-ros`.

---

## 26. Grasp Detection — ur_grasp Package

The `ur_grasp` package provides two backends for detecting grasp poses from a point cloud:

### Backend 1: simple_grasping (primary)

`ros-humble-simple-grasping` is an apt-installable, CPU-only package that detects objects using PCL RANSAC and returns `moveit_msgs/Grasp[]` directly. It understands cylinders and boxes.

```bash
sudo apt install ros-humble-simple-grasping
```

The `FindObjects` action server detects objects and returns their shapes, poses, and pre-computed grasp poses ready for MTC.

### Backend 2: Numpy centroid (fallback)

When `simple_grasping` is unavailable or fails, `ur_grasp` falls back to a colour-based centroid estimator:

1. Subscribe to `/camera_head/depth/color/points`
2. HSV threshold to isolate the target colour
3. Z-passthrough to remove floor/ceiling
4. Compute centroid (x, y)
5. `grasp_z = min_z + 0.30 * height` (30% from bottom gives best 2F-85 finger contact)

### Grasp Height Rule

For a Robotiq 2F-85 on cylinders: grasp at **30% from the bottom** of the object. Too high → fingers above the cylinder. Too low → fingers hit the table.

### Service Interface

```bash
# Detect and optionally execute a grasp
ros2 run ur_grasp grasp_node --ros-args -p colour:=red
python3 testing/test_grasp.py --colour red --execute
```

The node publishes `/ur_grasp/grasp_pose` (PoseStamped) and `/ur_grasp/grasp_marker` (MarkerArray for RViz).

---

## 27. Data Collection for Behavior Cloning — ur_data_collector

### What It Records

The `ur_data_collector` node subscribes to:
- `/joint_states` — arm joint positions at 50 Hz
- `/camera_head/color/image_raw` — RGB frames at 30 Hz

It saves synchronized episodes to HDF5 files at `~/ur3_demos/`.

### HDF5 Episode Format

```
demo_20260326_143201.h5
├── rgb_images      (N, H, W, 3)   uint8
├── joint_positions (N, 6)         float32
├── gripper_positions (N,)         float32
└── timestamps      (N,)           float64
```

### Usage

```bash
# Start the node
ros2 launch ur_data_collector data_collector.launch.py

# Record a demonstration
ros2 service call /data_collector/start_recording std_srvs/srv/Trigger
# ... perform the task manually or run pick_cylinders.py ...
ros2 service call /data_collector/stop_recording std_srvs/srv/Trigger

# Train a behavior cloning policy
python3 ur_data_collector/scripts/train_bc.py --data_dir ~/ur3_demos/
```

### Not a Playback System

The data collector **records only** — it does not replay trajectories. The HDF5 format is designed for offline training of BC/VLA models. For playback, use the trajectory from a completed MTC task or replay via `ros2 bag`.

---

## 28. Sequential Pick-and-Place with Python MoveIt Client

### Architecture

The `testing/pick_cylinders.py` script drives the robot using the MoveIt action client directly from Python, without MTC:

```
pick_cylinders.py
  → MoveGroup action (/move_group/... via MotionExecutor)
  → arm_controller (FollowJointTrajectory)
  → gripper_controller (GripperCommand)
```

### Key Design Decisions

**`rclpy.spin()` in daemon thread** — Using `spin_once(0.1)` in the main loop causes action result callbacks to never fire (30s timeout). Must use `rclpy.spin()` in a daemon thread:

```python
import threading
spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
spin_thread.start()
```

**`optional=True` on home-return steps** — Pilz PTP rejects zero-duration trajectories. If the arm is already at the home pose, the plan fails. Marking home-return steps as optional prevents the whole sequence from aborting.

**IK seed steering** — KDL IK returns solutions closest to the seed. Seeding with `shoulder_pan = atan2(target_y, target_x)` gives natural, non-wrapped solutions.

### Hierarchical Step Sequence

```
INIT → PRE_GRASP → DESCEND → GRASP → LIFT → TRANSPORT → LOWER → RELEASE → RETREAT → RETURN
```

Each step is a dict with `name`, `type` (arm/gripper), `pose`/`joints`, and optional `carry_z`.

---

## 29. MTC Humble vs Jazzy Compatibility

### API Differences

| Feature | Humble (MTC 2.5) | Jazzy (MTC 2.7+) |
|---|---|---|
| `PipelinePlanner` constructor | `(node, pipeline_id_map)` | `(node)` then `setPipeline()` |
| `create_service` QoS | needs explicit `rclcpp::QoS` object | accepts integer depth |
| `ExecuteTaskSolutionCapability` | built separately from `capabilities/` package | included in `moveit_task_constructor_core` |
| Stage property setters | `setProperty("key", value)` | same |

### Building MTC from Source on Humble

The system `ros-humble-moveit-task-constructor-*` packages lack the `capabilities` package (which provides `ExecuteTaskSolutionCapability` for move_group). Build from source:

```bash
# In your workspace src/:
git clone https://github.com/ros-planning/moveit_task_constructor.git
colcon build --packages-select \
  moveit_task_constructor_msgs \
  rviz_marker_tools \
  moveit_task_constructor_core \
  moveit_task_constructor_capabilities \
  moveit_task_constructor_visualization
```

Without `capabilities`, move_group logs:
```
Exception while loading move_group capability 'move_group/ExecuteTaskSolutionCapability': ... does not exist
```
MTC task execution will fail silently (plan succeeds but execution never fires).

### `PipelinePlanner` on Humble

```cpp
// Humble API:
std::unordered_map<std::string, std::string> pipeline_map = {
  {"ompl", "ompl_interface/OMPLPlanner"}
};
auto planner = std::make_shared<mtc::solvers::PipelinePlanner>(node, pipeline_map);

// Jazzy API (different signature — check at compile time):
auto planner = std::make_shared<mtc::solvers::PipelinePlanner>(node);
planner->setPlannerId("ompl[RRTConnect]");
```
