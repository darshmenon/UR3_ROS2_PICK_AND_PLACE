# Robotiq 2F-85 Gripper — UR3 Integration Reference

Everything specific to the Robotiq 2F-85 gripper: URDF structure, mimic joints, ROS 2 control, and how grasping works in simulation.

---

## Hardware Overview

The Robotiq 2F-85 is a **parallel two-finger adaptive gripper** with an 85 mm stroke. It has one motor driving both fingers symmetrically through a 4-bar linkage mechanism.

- **Max opening:** 85 mm
- **Max grip force:** 235 N
- **Finger stroke:** 0–85 mm (maps to `finger_joint` 0.0–0.8 rad in URDF)

---

## URDF Structure

Source: `robotiq_2f_85_gripper_visualization/urdf/robotiq_arg2f_85_model_macro.xacro`

```
robotiq_arg2f_base_link  (attached to tool0)
├── left_outer_knuckle   [revolute, mimic finger_joint ×1]
│   └── left_outer_finger [fixed]
│       └── left_inner_finger [revolute, mimic finger_joint ×-1]
│           └── left_inner_finger_pad [fixed]
├── right_outer_knuckle  [revolute, mimic finger_joint ×1]
│   └── right_outer_finger [fixed]
│       └── right_inner_finger [revolute, mimic finger_joint ×-1]
│           └── right_inner_finger_pad [fixed]
├── left_inner_knuckle   [revolute, mimic finger_joint ×1]
└── right_inner_knuckle  [revolute, mimic finger_joint ×1]
```

> The inner knuckles connect directly to the base (not through the outer finger chain). This is a URDF simplification of the physical 4-bar linkage — it approximates the real mechanism using mimic constraints.

---

## Joints

| Joint | Type | Range | Driven by |
|-------|------|-------|-----------|
| `finger_joint` | revolute | [0.0, 0.8] rad | `gripper_controller` (actuated) |
| `left_outer_knuckle_joint` | revolute | [0, 0.81] | mimic × +1 |
| `left_inner_knuckle_joint` | revolute | [0, 0.8757] | mimic × +1 |
| `left_inner_finger_joint` | revolute | [-0.8757, 0] | mimic × -1 |
| `right_outer_knuckle_joint` | revolute | [0, 0.81] | mimic × +1 |
| `right_inner_knuckle_joint` | revolute | [0, 0.8757] | mimic × +1 |
| `right_inner_finger_joint` | revolute | [-0.8757, 0] | mimic × -1 |

**URDF mimic tag example:**

```xml
<joint name="left_inner_knuckle_joint" type="revolute">
  <limit lower="0" upper="0.8757" velocity="2.0" effort="1000"/>
  <mimic joint="finger_joint" multiplier="1" offset="0"/>
</joint>
```

---

## Position Constants

Defined in `ur_llm_planner/ur_llm_planner/motion_executor.py`:

```python
GRIPPER_OPEN   = 0.0   # finger_joint fully open  (0 mm stroke)
GRIPPER_CLOSED = 0.8   # finger_joint fully closed (85 mm stroke)
GRIPPER_HALF   = 0.4   # half stroke
```

---

## ROS 2 Controller

Type: `position_controllers/GripperActionController`

Configured in `moveit_config/config/ros2_controllers.yaml`:

```yaml
gripper_controller:
  ros__parameters:
    type: position_controllers/GripperActionController
    joint: finger_joint
```

Exposes the action server: `/gripper_controller/gripper_cmd` (`control_msgs/action/GripperCommand`)

**Goal message:**

```python
from control_msgs.action import GripperCommand

goal = GripperCommand.Goal()
goal.command.position   = 0.8    # target finger_joint position (rad)
goal.command.max_effort = 50.0   # N (0 = use controller default)
```

---

## Mimic Joints in Ignition Gazebo

When the robot URDF is spawned into Ignition Gazebo via `ros_gz_sim` from the `/robot_description` topic, the URDF-to-SDF converter translates `<mimic>` tags into native Ignition physics joint constraints.

- **`robot_state_publisher`** reads `finger_joint` from `/joint_states` and derives all mimic joint TF transforms → correct visual in RViz.
- **Ignition physics** enforces mimic constraints directly — no plugin needed.
- **Old Gazebo Classic plugins** (`libgazebo_mimic_joint_plugin.so`, `libroboticsgroup_gazebo_mimic_joint_plugin.so`) are still referenced in the URDF but are dead code — they never load in Ignition. They are harmless.

---

## Grasp Behavior — Stall Detection

When closing the gripper on an object:

1. `GripperActionController` sends `finger_joint` toward 0.8 rad
2. The finger makes contact with the object and stalls
3. The joint velocity drops to zero with position error still present
4. The controller returns **`STATUS_ABORTED`** (stalled)

**This is correct and expected.** `ABORTED` means the gripper stalled on the object — the grasp succeeded. The code treats `ABORTED` as success:

```python
status = result.status
# SUCCEEDED = reached target (no object / very thin)
# ABORTED   = stalled on object = successful grasp
return status in (GoalStatus.STATUS_SUCCEEDED, GoalStatus.STATUS_ABORTED)
```

Only `STATUS_TIMED_OUT` (controller unresponsive) is treated as a real failure.

---

## Gripper in MoveIt Planning

The `gripper` planning group contains only `finger_joint`. It has **no IK solver** configured (KDL only works for kinematic chains — a single joint is not a chain).

Gripper motion is always sent **directly via the action server**, not through MoveIt:

```python
# DO NOT use:  move_group.set_named_target("closed")  ← sends to move_group, slow
# DO use:      GripperCommand action directly          ← fast, direct
```

All arm link vs gripper link collision pairs are disabled in the SRDF so MoveIt's collision checker does not flag false self-collisions when the gripper is open or closed.

---

## Transmission

From `robotiq_arg2f_transmission.xacro`:

```xml
<transmission name="finger_joint_trans">
  <type>transmission_interface/SimpleTransmission</type>
  <joint name="finger_joint">
    <hardwareInterface>PositionJointInterface</hardwareInterface>
  </joint>
  <actuator name="finger_joint_motor"/>
</transmission>
```

The hardware interface exposes only the `position` command interface for `finger_joint`. No velocity or effort interface is available for the gripper on this setup.

---

## Testing the Gripper

```bash
source install/setup.bash

# Open gripper
ros2 action send_goal /gripper_controller/gripper_cmd \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.0, max_effort: 50.0}}"

# Close gripper
ros2 action send_goal /gripper_controller/gripper_cmd \
  control_msgs/action/GripperCommand \
  "{command: {position: 0.8, max_effort: 50.0}}"

# Check finger_joint state
ros2 topic echo /joint_states --once | grep -A2 finger
```

---

## Common Gripper Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ABORTED` when closing on nothing | Joint reached limit, treated as stall | Fine — if no object present, it just fully closes |
| Mimic joints not moving in RViz | `robot_state_publisher` not receiving `/joint_states` | Check `joint_state_broadcaster` is active |
| Gripper not spawning | `gripper_controller` spawner fired before controller_manager ready | Increase spawn delay (currently 45s) |
| Gripper closes but object falls | Object too small / grasp height wrong | Lower grasp z (closer to block top), increase `max_effort` |
| `CONTROL_FAILED` on gripper | Timestamps zero — should not happen with `GripperCommand` action | Check controller is active: `ros2 control list_controllers` |
