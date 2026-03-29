# MoveIt 2 — UR3 Configuration Reference

Everything specific to how MoveIt 2 is configured and used for the UR3 arm in this project.

---

## Planning Groups (SRDF)

Defined in `moveit_config/config/ur.srdf`:

| Group | Type | Base Link | Tip Link | Joints |
|-------|------|-----------|----------|--------|
| `arm` | Chain | `torso_link` | `wrist_3_link` | 6 arm joints |
| `gripper` | Joints | — | — | `finger_joint` only |
| `arm_with_gripper` | Chain | `torso_link` | `tool0` | 6 arm + gripper |

> **Use `arm` for all motion planning.** `arm_with_gripper` adds the gripper tip frame but currently has no IK solver configured and is not used for planning.

---

## Named Poses (SRDF)

```xml
<!-- arm group -->
<group_state name="home" group="arm">
  <joint name="shoulder_pan_joint"  value="0"/>
  <joint name="shoulder_lift_joint" value="-1.5707963"/>
  <joint name="elbow_joint"         value="1.5707963"/>
  <joint name="wrist_1_joint"       value="-1.5707963"/>
  <joint name="wrist_2_joint"       value="-1.5707963"/>
  <joint name="wrist_3_joint"       value="0"/>
</group_state>

<!-- gripper group -->
<group_state name="open"   group="gripper"> <joint name="finger_joint" value="0.0"/> </group_state>
<group_state name="closed" group="gripper"> <joint name="finger_joint" value="0.8"/> </group_state>
```

Move to a named pose in Python:

```python
req.pipeline_id = "pilz_industrial_motion_planner"
req.planner_id  = "PTP"
req.goal_constraints = [joint_constraints_for("arm", "home")]
```

---

## Joint Names and Limits

```
shoulder_pan_joint   [-2π,  2π]   vel: 3.14 rad/s   effort: 56 N·m
shoulder_lift_joint  [-2π,  2π]   vel: 3.14 rad/s   effort: 56 N·m
elbow_joint          [ -π,   π]   vel: 3.14 rad/s   effort: 28 N·m   ← tighter limit
wrist_1_joint        [-2π,  2π]   vel: 6.28 rad/s   effort: 12 N·m
wrist_2_joint        [-2π,  2π]   vel: 6.28 rad/s   effort: 12 N·m
wrist_3_joint        [-2π,  2π]   vel: 6.28 rad/s   effort: 12 N·m
```

`elbow_joint` has the tightest range (`±π`). Pilz LIN motions that swing the elbow far frequently violate this — use Pilz PTP instead.

---

## IK Solver

Configured in `moveit_config/config/kinematics.yaml`:

```yaml
arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.005
```

KDL is a **local, gradient-descent IK solver**. It finds the nearest valid configuration to its seed state. Always seed it with the current joint state and override `shoulder_pan` to point at the target:

```python
seed.shoulder_pan_joint = math.atan2(target_y, target_x)
```

Without a good seed, KDL can return a valid but highly-wrapped solution (e.g. `shoulder_lift = -6.03 rad` instead of `-1.57 rad`), causing Pilz PTP to plan a huge unnecessary rotation.

> **Not installed:** `trac_ik` and `bio_ik` — both cause SIGABRT on import in Humble.
> **Do not add** `gripper` or `arm_with_gripper` to `kinematics.yaml` — KDL only works for kinematic chains with all joints in the URDF chain.

---

## Planning Pipeline — What's Used

| Pipeline | Plugin | Planner | Used? |
|----------|--------|---------|-------|
| `pilz_industrial_motion_planner` | `pilz_industrial_motion_planner/CommandPlanner` | **PTP** | ✅ All arm moves |
| `pilz_industrial_motion_planner` | same | LIN | ⚠️ Loads, fails for large elbow swings |
| `ompl` | `ompl_interface/OMPLPlanner` | RRTConnect (default) | ✅ Configured, IPTP time-stamping |
| `stomp` | `stomp_moveit/StompPlanner` | — | ❌ Not installed in Humble |

**All motion in this project uses Pilz PTP.** For Cartesian targets, we call `/compute_ik` first then send the joint solution to Pilz PTP.

---

## Motion Flow — Pick and Place

```
1. move_to_named_pose("arm", "home")
      → Pilz PTP to home joints from SRDF

2. open_gripper()
      → GripperCommand action: finger_joint = 0.0

3. move_to_pose(pre_grasp_pose)         # x, y, z+0.12 above block
      → /compute_ik  →  joint solution
      → Pilz PTP to joint solution

4. move_to_pose(grasp_pose)             # x, y, z+0.01 above block top
      → /compute_ik  →  joint solution
      → Pilz PTP to joint solution

5. close_gripper()
      → GripperCommand action: finger_joint = 0.8
      → Returns ABORTED (stall on object) = SUCCESS

6. move_to_pose(lift_pose)              # same x, y, z+0.15
      → /compute_ik  →  joint solution
      → Pilz PTP to joint solution

7. move_to_pose(place_pose)             # target x, y, z+0.12
      → /compute_ik  →  joint solution
      → Pilz PTP

8. open_gripper()                       # release

9. move_to_named_pose("arm", "home")    # return home
```

---

## Controllers

Configured in `moveit_config/config/moveit_controllers.yaml`:

```yaml
moveit_simple_controller_manager:
  controller_names:
    - arm_controller
    - gripper_controller

  arm_controller:
    type: FollowJointTrajectory
    joints: [shoulder_pan_joint, shoulder_lift_joint, elbow_joint,
             wrist_1_joint, wrist_2_joint, wrist_3_joint]

  gripper_controller:
    type: GripperCommand
    joints: [finger_joint]
```

> `arm_with_gripper_controller` was previously in `controller_names` with no matching config — caused SIGABRT on startup. It has been removed.

---

## Allowed Start Tolerance

```yaml
# moveit_controllers.yaml
trajectory_execution:
  allowed_start_tolerance: 0.1
```

If the robot's actual joint positions differ from the trajectory's first waypoint by more than 0.1 rad, execution is rejected. Increase if controllers drift (e.g. after a failed motion).

---

## SRDF — Collision Disable Matrix

Adjacent links are disabled automatically. Extra entries required because Pilz PTP checks the **entire straight-line path** in joint space:

| Arm link | Disabled with | Reason |
|----------|---------------|--------|
| `wrist_3_link` | all 11 gripper links | Adjacent / Always touching |
| `wrist_2_link` | all 11 gripper links | Near gripper base |
| `wrist_1_link` | all 11 gripper links | Near gripper base |
| `forearm_link` | all 11 gripper links | Collision during open-gripper arm motion |
| `upper_arm_link` | all 11 gripper links | Collision during return-to-home from grasp |
| `shoulder_link` | all 11 gripper links | Collision at extreme arm configurations |
| `base_link` | all 11 gripper links | Redundant safety |

The 11 gripper links are: `robotiq_arg2f_base_link`, `left_outer_knuckle`, `left_outer_finger`, `left_inner_knuckle`, `left_inner_finger`, `left_inner_finger_pad`, `right_outer_knuckle`, `right_outer_finger`, `right_inner_knuckle`, `right_inner_finger`, `right_inner_finger_pad`.

Missing any of these causes `INVALID_MOTION_PLAN (-2)` from Pilz.

---

## Debugging Quick Reference

```bash
# Check if move_group is up and planners loaded
ros2 node info /move_group | grep -E "service|action"

# Check which controllers are active
ros2 control list_controllers

# Check the Allowed Collision Matrix
ros2 service call /get_planning_scene moveit_msgs/srv/GetPlanningScene \
  "{components: {components: 128}}"

# Watch joint states
ros2 topic echo /joint_states --once

# Watch move_group logs for planning errors
ros2 topic echo /rosout | grep -E "OMPL|Pilz|error|abort" -i

# Test IK manually
ros2 service call /compute_ik moveit_msgs/srv/GetPositionIK \
  "{ik_request: {group_name: arm, pose_stamped: {header: {frame_id: base_link}, \
   pose: {position: {x: 0.25, y: 0.10, z: 0.20}, \
          orientation: {x: 1.0, y: 0.0, z: 0.0, w: 0.0}}}}}"
```

---

## Common Errors

| Error Code | Value | Likely Cause | Fix |
|------------|-------|--------------|-----|
| `CONTROL_FAILED` | -4 | Zero timestamps (TOTG bug) | Use Pilz PTP or IPTP adapter |
| `INVALID_MOTION_PLAN` | -2 | Pilz detected self-collision on path | Add `disable_collisions` to SRDF |
| `PLANNING_FAILED` | -1 | No valid plan found | Check IK seed, increase planning time |
| `TIMED_OUT` | -6 | TF time jump or controller not responding | Wait 10s after restart |
| `GOAL_TOLERANCE_VIOLATED` | — | Controller couldn't track trajectory | Lower velocity/acceleration scaling |
