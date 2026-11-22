# ur_openvla

OpenVLA vision-language-action control. `inference_node.py` feeds the camera image and a task string to `openvla/openvla-7b` (about 15 GB download on first run) and turns the 7-D output (6 arm joint deltas plus gripper) into motion.

## Interface

- Subscribes `/joint_states` and the camera image topic.
- Publishes `/arm_controller/joint_trajectory`; sends gripper goals to `/gripper_controller/gripper_cmd`.
- Params: `task` (default "pick the red block and place it in the bin"), `checkpoint` (`openvla/openvla-7b`), `camera_topic` (`/camera_head/color/image_raw`), `control_hz` (10), `action_scale` (0.05), `enabled`, `use_sim_time`.

## Run

```bash
ros2 launch ur_openvla openvla_inference.launch.py task:="pick the red block and place it in the bin"
```

Needs torch and transformers installed and the simulation running. Mutually exclusive with the other policy "brains" (LLM, RL, flow).
