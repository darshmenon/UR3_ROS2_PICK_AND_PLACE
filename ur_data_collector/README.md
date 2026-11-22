# ur_data_collector

Records demonstrations for behaviour cloning and VLA fine-tuning, and holds the training and export scripts.

## Node

`collector_node.py` buffers `/joint_states`, `/camera_head/color/image_raw` and (optionally) `/camera_head/depth/image_rect_raw` while recording, and writes one HDF5 file per episode.

- Services `/data_collector/start_recording` and `/data_collector/stop_recording` (Trigger).
- Params (`config/collector_params.yaml`): `output_dir` (`~/ur3_demos`), `image_height`, `image_width`, `record_depth`, `episode_name_prefix`.

## Scripts

- `auto_collect_demos.py`: repeatedly triggers the MTC `run_pick_place` service while recording, and sorts episodes by success.
- `train_bc.py`: CNN + MLP behaviour cloning on the HDF5 files.
- `export_lerobot_dataset.py`: converts demos to a LeRobotDataset.
- `train_act.py`: wrapper around `lerobot-train` for ACT (needs a separate Python 3.12 venv with LeRobot).

## Run

```bash
ros2 launch ur_data_collector data_collector.launch.py
ros2 service call /data_collector/start_recording std_srvs/srv/Trigger {}
ros2 service call /data_collector/stop_recording std_srvs/srv/Trigger {}
python3 ur_data_collector/scripts/train_bc.py --data_dir ~/ur3_demos --output_dir ~/bc_policy --epochs 50
```
