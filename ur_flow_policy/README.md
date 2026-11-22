# ur_flow_policy

Flow-matching action-chunk policy with a frozen DINOv2 image encoder for UR3 pick and place, trained on `ur_data_collector` HDF5 demos.

## Contents

- `ur_flow_policy/model.py`: `FlowMatchingPolicy`.
- `scripts/train_flow_policy.py`: trains on demo files, windowed into action chunks.
- `inference_node.py`: each tick encodes the camera image once, samples an action chunk with an Euler ODE solver, blends overlapping chunks (temporal ensembling), publishes arm trajectories and sends gripper commands to `/gripper_controller/gripper_cmd`. Reads `/joint_states`.

## Launch

`flow_policy_inference.launch.py` args: `checkpoint`, `camera_topic` (default `/camera_head/color/image_raw`), `control_hz` (10), `action_scale` (1.0), `chunk_size` (16), `ode_steps` (10), `temporal_ensemble_m` (0.1), `dinov2_backbone` (`facebook/dinov2-base`).

## Run

```bash
python3 scripts/train_flow_policy.py --data_dir ~/ur3_demos --output_dir ~/flow_policy --epochs 100
ros2 launch ur_flow_policy flow_policy_inference.launch.py checkpoint:=/path/to/best_policy.pt
```

Mutually exclusive with the other policy "brains" (LLM, RL, OpenVLA).
