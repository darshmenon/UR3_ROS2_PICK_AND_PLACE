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

## Testing Scripts

| Script | Purpose |
|--------|---------|
| `testing/test_pick.py` | Full pick-and-place test without LLM — hardcoded blue block position |
| `testing/test_steps.py` | Step-by-step test: runs each motion action individually to isolate failures |

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
```
