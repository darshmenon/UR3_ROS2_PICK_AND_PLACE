# ur_force_control

Force and impedance control for the UR3: joint and Cartesian impedance controllers, an external wrench estimator, a gripper force monitor, and a peg-in-hole task. See `PEG_IN_HOLE.md` for the peg-in-hole recording workflow.

## Nodes

- `joint_impedance_controller` (C++, Pinocchio): joint-space impedance with gravity compensation; topics/params include `stiffness`, `damping`, `effort_limits`, `publish_rate_hz`, `gravity_scale`; service `hold_pose` (Trigger).
- `cartesian_impedance_controller` (C++): `tau = J^T [K (x_des - x) - D v] + g(q)`. Inputs `~/target_pose` (PoseStamped) and `~/stiffness` (6 values); output `~/tip_pose`; service `~/hold_current_pose`. Params `tip_frame` (default `peg_tip`), `m_eff_lin`, `m_eff_rot`, `joint_damping`, `publish_rate_hz` (500).
- `external_wrench_estimator` (C++): estimates the end-effector wrench from joint efforts. Publishes `/ft/estimated_wrench` and `/ft/arm_contact_detected`; service `/ft/zero_wrench`. Params `planning_group`, `force_threshold_n`, `damping_lambda`.
- `ft_monitor_node`: watches finger effort, publishes `/ft/finger_effort` and `/ft/contact_detected`, and offers `/ft/compliant_close` (close until contact). Params `effort_threshold`, `close_step`, `step_interval_s`, `max_effort_limit`.
- `peg_in_hole_task`: descends over a hole and optionally spiral-searches, driving the Cartesian controller and logging a CSV.

`scripts/` has the MuJoCo peg-in-hole scripts, a Gazebo recorder (`record_peg_in_hole.py`) and a Drake dynamics check.

## Launch files

`joint_impedance.launch.py`, `wrench_estimator.launch.py`, `ft_monitor.launch.py`.

## Run

```bash
ros2 launch ur_force_control wrench_estimator.launch.py
ros2 launch ur_force_control joint_impedance.launch.py
ros2 run ur_force_control peg_in_hole_task --ros-args -p use_sim_time:=true -p search:=true
```
