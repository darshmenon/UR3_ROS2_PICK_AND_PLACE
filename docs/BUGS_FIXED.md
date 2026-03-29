# Bugs Fixed — UR3 ROS2 Pick and Place

## Session: 2026-03-21

### 1. TOTG Zero-Duration Trajectory Bug (CONTROL_FAILED)
**File:** `ur_llm_planner/ur_llm_planner/motion_executor.py`
**Error:** `arm_controller: Time between points 0 and 1 is not strictly increasing, it is 0.000000 and 0.000000`
**Root cause:** MoveIt2 Humble's `AddTimeOptimalParameterization` response adapter fails silently for some OMPL trajectories, leaving all `time_from_start = 0`. The JointTrajectoryController then rejects the trajectory.
**Fix:** Switch all joint-space moves (`move_to_named_pose`) to use Pilz PTP planner which generates its own timestamps without relying on TOTG. Switch Cartesian moves (`move_to_pose`) to use IK service (`/compute_ik`) → joint values → Pilz PTP.

---

### 2. Default Planning Pipeline is Pilz, Not OMPL (PLANNING_FAILED)
**File:** `ur_llm_planner/ur_llm_planner/motion_executor.py`
**Error:** `Using planning pipeline 'pilz_industrial_motion_planner'` for Cartesian moves; Pilz LIN then fails with `elbow_joint velocity 13.9627 > limit 3.14159`
**Root cause:** When `pipeline_id = ""` in the MoveGroup request, Humble defaults to Pilz (not OMPL), and Pilz LIN fails because the straight-line Cartesian path requires very high joint velocities.
**Fix:** Removed explicit Pilz LIN from `move_to_pose`; replaced with IK+Pilz PTP approach (see Bug #1 fix).

---

### 3. Self-Collision: upper_arm_link vs Gripper Fingers (INVALID_MOTION_PLAN)
**File:** `moveit_config/config/ur.srdf`
**Error:** `MoveGroup returned error code -2 (INVALID_MOTION_PLAN)` when moving arm from grasp position back to home
**Root cause:** The SRDF was missing `<disable_collisions>` entries for `upper_arm_link` vs all 10 Robotiq 2F-85 gripper links. MoveIt detected false self-collisions along the path, causing Pilz to reject the plan.
**Fix:** Added 11 `<disable_collisions reason="Never">` entries for `upper_arm_link` vs all gripper finger/knuckle/base links.

---

### 4. RViz2 SIGSEGV on Launch (exit code -11)
**File:** `ur_gazebo/launch/ur.gazebo.launch.py`
**Error:** `process has died [pid ..., exit code -11]` — RViz2 segfaults when MoveIt MotionPlanning plugin loads
**Root cause:** Known MoveIt2 Humble bug in `MotionPlanningDisplay` when certain planning pipelines are active.
**Fix:** Added `moveit_config.planning_pipelines` to RViz2 node parameters (provides full pipeline info so plugin doesn't dereference null). Added `use_rviz:=false` launch argument to skip RViz2 for faster headless testing.

---

### 5. Wrong Default World (no blue block)
**File:** `ur_gazebo/launch/ur.gazebo.launch.py`
**Error:** Default world `pick_and_place_demo.world` has no blue block
**Fix:** Changed default world to `colored_blocks.world` which contains red, green, and blue blocks at known positions.

---

### 6. Gripper Controller Spawner Race Condition
**File:** `ur_gazebo/launch/ur.gazebo.launch.py`
**Error:** `RuntimeError: Could not successfully call service /controller_manager/list_controllers after 3 attempts`
**Root cause:** Timing — the spawner fired too early before the Gazebo controller_manager was fully ready.
**Fix:** Changed spawner delays to `[35s, 40s, 45s]` for `[joint_state_broadcaster, arm_controller, gripper_controller]`.

---

### 7. Perception: depth_scale = 0.001 (wrong units)
**File:** `ur_perception/ur_perception/object_detector_node.py`
**Error:** All detected object depths were 1000x too small
**Root cause:** Gazebo publishes depth images in metres (float32), not millimetres (uint16). `depth_scale=0.001` was for RealSense hardware, not simulation.
**Fix:** `depth_scale = 1.0`

---

### 8. Camera Info QoS Mismatch
**File:** `ur_perception/ur_perception/object_detector_node.py`
**Error:** Camera info never received; `TRANSIENT_LOCAL` subscriber can't receive from `VOLATILE` publisher
**Root cause:** ros_gz_bridge publishes camera_info with `VOLATILE` durability, but the subscriber was `TRANSIENT_LOCAL`.
**Fix:** Changed subscriber QoS durability to `VOLATILE`.

---

### 9. LLM Planner: Executor Deadlock
**File:** `ur_llm_planner/ur_llm_planner/motion_executor.py`
**Error:** `rclpy.spin_until_future_complete` called from background thread while `rclpy.spin` ran on the same node → deadlock
**Fix:** Replaced all `spin_until_future_complete` calls with `threading.Event` pattern: `future.add_done_callback(lambda _: event.set()); event.wait(timeout=...)`.

---

### 10. Camera Bridge: Wrong Ignition Topic Paths
**File:** `ur_gazebo/config/ros_gz_bridge.yaml`, `ur_gazebo/launch/ur.gazebo.launch.py`
**Error:** Camera images/depth never bridged to ROS
**Root cause:** Ignition Gazebo sensor topics use the full world/model/link path: `/world/default/model/ur/link/base_link/sensor/camera_head/image`, not short names.
**Fix:** Updated all gz_topic_name entries and image_bridge arguments to use the full path.

---

### 11. Self-Collision: forearm_link / shoulder_link vs Gripper (INVALID_MOTION_PLAN in step 7)
**File:** `moveit_config/config/ur.srdf`
**Error:** `MoveGroup returned error code -2 (INVALID_MOTION_PLAN)` when moving to pre-grasp with gripper OPEN
**Root cause:** When the gripper fingers are open, their collision geometry extends outward and triggers false collision detection against `forearm_link` and `shoulder_link` during planning. The SRDF only had `upper_arm_link` covered (Bug #3) but not these two arm links.
**Fix:** Added 11 `<disable_collisions reason="Never">` entries each for `forearm_link` and `shoulder_link` vs all gripper finger/knuckle/base links (total 22 new entries).

---

### 13. IK Solver (KDL) Finding Behind-the-Back Solutions (INVALID_MOTION_PLAN)
**File:** `ur_llm_planner/ur_llm_planner/motion_executor.py`
**Error:** `MoveGroup returned error code -2 (INVALID_MOTION_PLAN)` when going to pre-grasp or returning to home from grasp position
**Root cause:** KDL IK defaulted to zero-config seed, finding solutions with `shoulder_pan=3.953` (226°) — the arm reaching "behind" itself. Pilz PTP's straight-line path from this configuration to home passed through self-colliding intermediate states.
**Fix:** Seed the IK request with the current joint state (`robot_state.joint_state`) and override `shoulder_pan` to `atan2(target_y, target_x)` so KDL converges to the "front-side" IK solution.

---

### 14. IK Normalization: Python Banker's Rounding Leaves Wrist 2π Away (INVALID_MOTION_PLAN)
**File:** `ur_llm_planner/ur_llm_planner/motion_executor.py`
**Error:** `MoveGroup returned error code -2 (INVALID_MOTION_PLAN)` during place — wrist joints changed by ~180°, causing mid-path collision
**Root cause:** KDL can return 2π-equivalent joint values (e.g., wrist_2=4.712 vs -1.571). The normalization used `round(diff/2π)` but Python's banker's rounding returns `round(0.5)=0` instead of 1, leaving the value one full revolution away from the current state.
**Fix:** Use `math.floor(diff/(2π) + 0.5)` for round-half-up behaviour. Also added `_ARM_JOINT_LIMITS` and a post-normalization clamp to ensure `elbow_joint` stays within `[-π, π]`.

---

### 15. Stray Character in Gripper URDF (cosmetic XML bug)
**File:** `robotiq_2f_85_gripper_visualization/urdf/robotiq_arg2f_85_model_macro.xacro`
**Error:** Stray `f` character on line 109: `<origin xyz="0 0 0" rpy="0 0 0" />f` inside `inner_finger_pad` visual element
**Root cause:** Typo — stray character left in file; XML parsers tolerate it as a text node but it is invalid XML.
**Fix:** Removed the stray `f` character.

---

---

### 16. KDL IK Wraps Shoulder Joint for Negative-Y Targets (INVALID_MOTION_PLAN)
**File:** `ur_llm_planner/ur_llm_planner/motion_executor.py`
**Error:** `MoveGroup returned error code -2` when moving to green block (y < 0) from home pose
**Root cause:** KDL is a local solver. When the arm is at home with `elbow ≈ 0`, it finds a valid but degenerate solution: `shoulder_pan = -2.93 rad` (going the long way around) instead of `-0.17 rad`. Pilz PTP's straight-line path from that wrapped configuration collides or exceeds limits.
**Fix:** Detect `elbow < 0.3 rad` (arm at/near home) and inject a natural downward-grasp seed `[-99, -2.2, 2.2, -1.6, -1.571, 0]` with `shoulder_pan = atan2(target_y, target_x)`. KDL then converges to the correct "front-side" solution.

---

### 17. Gripper Mimic Joints: Right Side Stuck at Limits, Left Partially Closes
**File:** `moveit_config/config/ur.ros2_control.xacro`, `moveit_config/config/initial_positions.yaml`
**Error:** At sim startup, right outer/inner knuckle joints initialise at their maximum positions (stuck fully closed); left outer knuckle joint (`left_outer_knuckle_joint`) was missing from the `ros2_control` block entirely. Closing the gripper only partially moved one side.
**Root cause:** All mimic joints shared the key `${initial_positions['finger_joint']}`. Ignition Gazebo's SDF converter evaluated them as a single symbolic reference and initialised right-side joints at their URDF `upper` limits. Additionally, `left_outer_knuckle_joint` had no `<joint>` entry at all, so it had no state interface and Ignition never received an initial value for it.
**Fix:**
1. Added per-joint keys to `initial_positions.yaml` (`left_outer_knuckle_joint: 0.0`, `right_outer_knuckle_joint: 0.0`, etc.)
2. Updated every mimic joint in `ur.ros2_control.xacro` to reference its own key (e.g., `${initial_positions['right_outer_knuckle_joint']}`)
3. Added the missing `left_outer_knuckle_joint` entry to the xacro

---

## Known Remaining Issues

| # | Issue | File | Status |
|---|-------|------|--------|
| R1 | OMPL `CONTROL_FAILED` — `response_adapters` plugin system does not exist in MoveIt2 Humble (added in Iron). OMPL trajectories have no post-planning time parameterisation → timestamps=0 → `JointTrajectoryController` rejects them. **Workaround:** use Pilz PTP for all motion. | `moveit_config/config/ompl_planning.yaml` | Expected / won't fix on Humble |
| R2 | RViz2 MotionPlanningDisplay can segfault on startup with certain pipeline configs. **Workaround:** `use_rviz:=false` or pass full `planning_pipelines` param. | `ur_gazebo/launch/ur.gazebo.launch.py` | Mitigated |
| R3 | `stomp_moveit/StompPlanner` not installed for Humble (only Iron+). Logs a non-fatal error at startup. | `moveit_config/config/stomp_planning.yaml` | Not fixable on Humble |
| R4 | `occupancy_map_monitor/PointCloudOctomapUpdater` plugin not installed. Non-fatal log error at startup. No depth camera octomap needed for current demos. | `moveit_config/config/sensors_3d.yaml` | Accepted |
| R5 | Gripper mimic joints: despite the `initial_value` fix, Ignition Gazebo may still not perfectly enforce mimic physics constraints for the 4-bar linkage (depends on Ignition version). The URDF approximation uses mimic tags rather than the actual mechanical linkage. | `robotiq_2f_85_gripper_visualization/urdf/` | Cosmetic — grasping works |
| R6 | Standalone `ros2_control_node` in launch file crashes on startup (harmless — Gazebo provides its own controller_manager). | `ur_gazebo/launch/ur.gazebo.launch.py` | Harmless |

---

## Testing Scripts

| Script | Purpose |
|--------|---------|
| `testing/test_pick.py` | Full pick-and-place test without LLM — hardcoded blue block position |
| `testing/test_steps.py` | Step-by-step test: runs each motion action individually to isolate failures |
| `testing/test_planners.py` | Tests all planner+executor combinations: Pilz PTP, Pilz LIN, OMPL, gripper |
| `testing/teleop.py` | Keyboard teleoperation — joint mode and Cartesian mode, gripper keys |
| `testing/camera_view.py` | Live camera feed from Gazebo with optional HSV block detection overlay |

### Usage
```bash
source install/setup.bash

# Step-by-step test (identify which step fails):
python3 testing/test_steps.py all

# Single step:
python3 testing/test_steps.py 5   # move to pre-grasp

# Full pick test:
python3 testing/test_pick.py
python3 testing/test_pick.py 0.30 0.05 0.08  # custom position

# Test all planners:
python3 testing/test_planners.py

# Keyboard teleoperation:
python3 testing/teleop.py

# Live camera view (add --detect for HSV block detection overlay):
python3 testing/camera_view.py
python3 testing/camera_view.py --detect
```
