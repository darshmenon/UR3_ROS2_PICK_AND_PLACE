# Bug Fixes Log — UR3 ROS2 Pick and Place

All bugs encountered while getting `move_group` and `test_planning_execution` working on ROS 2 Humble + MoveIt 2 + Ignition Gazebo.

---

## Bug 1: move_group SIGABRT — dead controller in controller_names

**File:** `moveit_config/config/moveit_controllers.yaml`

**Symptom:** `move_group` crashes immediately with exit code -6 (SIGABRT).

**Root cause:** `arm_with_gripper_controller` was listed under `controller_names` but its config block was commented out. `moveit_simple_controller_manager` calls `std::terminate()` if any name in `controller_names` has no matching config block.

**Fix:** Removed `- arm_with_gripper_controller` from `controller_names`.

```yaml
# Before (broken)
controller_names:
  - arm_controller
  - gripper_controller
  - arm_with_gripper_controller   # <-- config block was commented out

# After (fixed)
controller_names:
  - arm_controller
  - gripper_controller
```

---

## Bug 2: move_group SIGABRT — trac_ik not installed

**File:** `moveit_config/config/kinematics.yaml`

**Symptom:** `move_group` crashes with exit code -6 (SIGABRT) after the controller fix.

**Root cause:** `kinematics.yaml` referenced `trac_ik_kinematics_plugin/TRAC_IKKinematicsPlugin` for the `arm` group, but `ros-humble-trac-ik-kinematics-plugin` is not installed on this machine.

**Fix:** Switched to `kdl_kinematics_plugin/KDLKinematicsPlugin`, which is always installed with MoveIt 2.

```yaml
# Before (broken)
arm:
  kinematics_solver: trac_ik_kinematics_plugin/TRAC_IKKinematicsPlugin

# After (fixed)
arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.1
  kinematics_solver_attempts: 3
```

---

## Bug 3: KDL kinematics error — gripper is not a chain

**File:** `moveit_config/config/kinematics.yaml`

**Symptom:** `move_group` logs errors about KDL being unable to solve IK for `gripper` and `arm_with_gripper` groups.

**Root cause:** KDL requires a single kinematic chain (base → tip). The `gripper` group is a parallel mechanism and `arm_with_gripper` is also not a simple chain — KDL cannot solve IK for either.

**Fix:** Removed `gripper` and `arm_with_gripper` entries from `kinematics.yaml` entirely. Only `arm` needs an IK solver.

---

## Bug 4: Wrong mesh paths in URDF

**File:** `moveit_config/config/ur.urdf`

**Symptom:** Gazebo reports `mesh file not found` for sensor meshes (e.g. `d435.stl`).

**Root cause:** The static `ur.urdf` file was generated on a different machine with `/home/darsh/` hardcoded in all mesh paths. This machine uses `/home/asimov/`.

**Fix:** Regenerated the URDF from the xacro source on the correct machine:

```bash
xacro moveit_config/config/ur.urdf.xacro > moveit_config/config/ur.urdf
```

---

## Bug 5: move_group SIGABRT — request_adapters as YAML list

**Files:** `moveit_config/config/ompl_planning.yaml`, `pilz_industrial_motion_planner_planning.yaml`, `stomp_planning.yaml`

**Symptom:** `move_group` crashes with:
```
terminate called after throwing an instance of 'rclcpp::exceptions::InvalidParameterTypeException'
  what(): parameter 'ompl.request_adapters' has invalid type: expected [string] got [string_array]
```
Same crash for `stomp.request_adapters` and `pilz_industrial_motion_planner.request_adapters`.

**Root cause:** All three planning pipeline config files defined `request_adapters` and `response_adapters` as YAML lists (string arrays). MoveIt 2 Humble expects a **single space-separated string**.

**Fix:** Changed all adapter fields from YAML list format to `>-` block scalar:

```yaml
# Before (broken)
request_adapters:
  - default_planning_request_adapters/ResolveConstraintFrames
  - default_planning_request_adapters/ValidateWorkspaceBounds

# After (fixed)
request_adapters: >-
  default_planner_request_adapters/ResolveConstraintFrames
  default_planner_request_adapters/FixWorkspaceBounds
```

---

## Bug 6: Wrong adapter plugin prefix — `default_planning_` vs `default_planner_`

**Files:** `ompl_planning.yaml`, `pilz_industrial_motion_planner_planning.yaml`, `stomp_planning.yaml`

**Symptom:** `move_group` logs:
```
Exception while loading planning adapter plugin 'default_planning_request_adapters/ResolveConstraintFrames':
... does not exist. Declared types are default_planner_request_adapters/...
```

**Root cause:** The config files used `default_planning_request_adapters/` (with "planning") but the installed package is `default_planner_request_adapters/` (with "planner"). Note: response adapters correctly use `default_planning_response_adapters/`.

**Fix:** Changed prefix from `default_planning_request_adapters/` to `default_planner_request_adapters/` in all three files.

---

## Bug 7: Wrong adapter plugin names — `Check*`/`Validate*` vs `Fix*`

**Files:** `ompl_planning.yaml`, `pilz_industrial_motion_planner_planning.yaml`, `stomp_planning.yaml`

**Symptom:** `move_group` logs errors loading `ValidateWorkspaceBounds`, `CheckStartStateBounds`, `CheckStartStateCollision`.

**Root cause:** These plugin names don't exist. The actual declared types in the installed package are:
- `FixWorkspaceBounds` (not `ValidateWorkspaceBounds`)
- `FixStartStateBounds` (not `CheckStartStateBounds`)
- `FixStartStateCollision` (not `CheckStartStateCollision`)

**Fix:** Updated all three config files to use the correct `Fix*` names.

---

## Non-Bug: ros2_control_node crash (harmless)

**File:** `ur_gazebo/launch/ur.gazebo.launch.py`

**Symptom:** `ros2_control_node` exits with code -6 (SIGABRT) shortly after launch.

**Why it's harmless:** The launch file starts a standalone `ros2_control_node` that tries to load `gz_ros2_control/GazeboSimSystem`. This plugin can only run inside the Gazebo process — it cannot load in a standalone node. Ignition Gazebo spawns its own controller_manager internally via the `gz_ros2_control` plugin in the robot's SDF. The controller spawners use `OnProcessStart` with time delays, which means they eventually connect to Gazebo's controller_manager. **No fix needed.**

---

## Bug 8: OMPL pipeline uses CHOMP instead — planning_plugins list vs string

**Files:** `ompl_planning.yaml`, `pilz_industrial_motion_planner_planning.yaml`, `stomp_planning.yaml`

**Symptom:** `move_group` loads but always uses CHOMP regardless of which pipeline is requested. Pose goals fail with:
```
[chomp_planner]: Only joint-space goals are supported
```

**Root cause:** `planning_plugins` (plural, YAML list) is not the parameter MoveIt 2 reads. MoveIt 2 Humble reads `planning_plugin` (singular, string). When it finds a list, it treats it as "multiple plugins available" and falls back to CHOMP (alphabetically first).

**Fix:** Changed from YAML list to a single string in all pipeline configs:

```yaml
# Before (broken) — CHOMP always used
planning_plugins:
  - ompl_interface/OMPLPlanner

# After (fixed) — OMPL used correctly
planning_plugin: ompl_interface/OMPLPlanner
```

Confirmed fix: `MoveGroup context using planning plugin ompl_interface/OMPLPlanner` in logs.

---

## Summary of Fixed Files

| File | Bug |
|------|-----|
| `moveit_config/config/moveit_controllers.yaml` | Dead controller in controller_names |
| `moveit_config/config/kinematics.yaml` | trac_ik not installed; gripper not a chain |
| `moveit_config/config/ur.urdf` | Wrong machine mesh paths |
| `moveit_config/config/ompl_planning.yaml` | List adapters, wrong prefix, wrong names, planning_plugin format |
| `moveit_config/config/pilz_industrial_motion_planner_planning.yaml` | List adapters, wrong prefix, wrong names, planning_plugin format |
| `moveit_config/config/stomp_planning.yaml` | List adapters, wrong prefix, wrong names, planning_plugin format |
| `moveit_config/config/ur.srdf` | Stale collision disable for non-existent link cylinder_1 |
