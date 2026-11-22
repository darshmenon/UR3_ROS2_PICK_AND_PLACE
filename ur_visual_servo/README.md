# ur_visual_servo

Position-based visual servoing. `servo_node` reads `/ur_grasp/grasp_pose` and the end-effector pose from TF, then sends small corrective joint-trajectory steps until a virtual TCP (tool0 plus `tcp_offset_xyz`) reaches the target, and optionally closes the gripper.

## Interface

- Services `/visual_servo/start` and `/visual_servo/stop` (Trigger); status on `/visual_servo/status`.
- Subscribes `/ur_grasp/grasp_pose`, `/joint_states`.
- Params: `servo_rate_hz` (5.0), `xy_tolerance` (0.006), `z_tolerance` (0.010), `step_size` (0.025), `grasp_offset_z` (0.05), `auto_grasp`, `max_iterations` (60), `ee_frame` (`tool0`), `tcp_offset_xyz` ([0, 0, 0.145]), `gripper_joint_name`, `gripper_fully_closed`, `gripper_stall_margin`. For OnRobot grippers use `gripper_joint_name:=gripper_joint`.

## Run

```bash
ros2 launch ur_visual_servo visual_servo.launch.py
ros2 service call /visual_servo/start std_srvs/srv/Trigger {}
```

Needs the simulation and `ur_grasp` publishing grasp poses.
