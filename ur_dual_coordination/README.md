# ur_dual_coordination

Whole-body coordination of the two UR3 arms carrying one object. A single node solves all 12 joints together (Pinocchio) so the hands keep their relative pose while the object follows a target.

## Node

`coordinator_node.py` runs at 50 Hz and streams short joint trajectories to `/left_arm_controller/joint_trajectory` and `/right_arm_controller/joint_trajectory` (params `left_topic`, `right_topic`).

- Subscribes: `/robot_description`, `/joint_states`, `/dual/object_target` (PoseStamped).
- Services: `/dual/grasp` (freeze the hands' relative pose), `/dual/release` (stop commanding).
- Publishes: `/dual/status`.
- Params: `rate_hz`, `max_object_speed` (0.05 m/s), `min_move_time`, `max_joint_speed`, `joint_state_timeout`, `resync_threshold`.

`controller.py` and `kinematics.py` hold the solver.

## Run

```bash
ros2 launch ur_dual_coordination dual_coordination.launch.py
ros2 service call /dual/grasp std_srvs/srv/Trigger {}
ros2 topic pub --once /dual/object_target geometry_msgs/msg/PoseStamped "{header: {frame_id: world}, pose: {position: {x: 0.2, y: 0.0, z: 0.35}, orientation: {w: 1.0}}}"
ros2 service call /dual/release std_srvs/srv/Trigger {}
```

Bring both hands to the object first (for example with the dual MTC pipeline). Needs the dual-arm Gazebo simulation.
