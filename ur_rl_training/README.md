# ur_rl_training

Reinforcement and imitation learning for UR3 pick and place in MuJoCo, plus a ROS 2 node that runs a trained SAC policy in Gazebo.

## Contents

- `envs/ur3_pick_place_env.py`, `envs/ur3_pick_place_env_v2.py`: Gymnasium environments (v2 fixes the reward so the policy does not stand still).
- `scripts/train.py`, `scripts/train_v2.py`: SAC training (stable-baselines3). Models go to `models/checkpoints/<run>/`.
- `scripts/expert_demos.py`: scripted expert that records successful transitions.
- `scripts/dagger.py`, `scripts/flow_policy.py`: behaviour cloning with DAgger, and a flow-matching action-chunk policy.
- `scripts/bc_mtc.py`: offline behaviour cloning on MTC demos recorded in Gazebo.
- `scripts/eval_policy.py`, `scripts/eval_headless.py`, `scripts/render_policy.py`: success-rate evaluation and GIF rendering.
- `ur_rl_training/policy_node.py` (`policy_node`): reads `/joint_states` and TF, publishes `/arm_controller/joint_trajectory`, and drives `/gripper_controller/gripper_cmd`. Also subscribes to `/ur_grasp/grasp_pose`.

## Launch

`rl_policy.launch.py` args: `model_path` (required), `object_x/y/z`, `drop_x/y/z`, `phase`, `base_frame`, `ee_frame`, `control_rate_hz`, `step_dt`.

## Run

```bash
cd ur_rl_training
python3 scripts/train_v2.py
python3 scripts/expert_demos.py --episodes 100 --out ~/ur3_rl_demos/expert.npz
python3 scripts/eval_policy.py --policy ~/ur3_rl_demos/flow.pt --episodes 50
ros2 launch ur_rl_training rl_policy.launch.py model_path:=<path/to/best_model.zip>
```

Training scripts block the system `triton` import to avoid a segfault when torch builds an optimizer.
