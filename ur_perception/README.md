# ur_perception

Camera perception for the UR3 pick and place stack: colour/YOLO object detection with depth-based 3-D poses, VLM text grounding, multi-view point cloud reconstruction, and a few PCL tools.

## Nodes

- `object_detector_node.py`: colour (optional YOLO) detector. Publishes `/detected_objects` (`ur_interfaces/DetectedObjectArray`), `/detection_image`, and box/cylinder collision objects to `/planning_scene`.
- `vlm_grounding_node.py`: asks an Ollama VLM (default `qwen2.5vl:3b`) for a box around the object named on `/vlm/query`, projects it with depth, and publishes `/vlm/target_pose` and `/vlm/target_object_id`.
- `object_reconstructor_node.py`: fuses wrist-camera point clouds into base_link using TF (optional ICP with open3d). Services `/ur_perception/reconstruct/start` and `/stop`; publishes `/ur_perception/reconstructed_points`; can save PLY/mesh.
- `reconstruct_sweep_node.py`: moves the wrist camera through joint-space viewpoints, picking the least-covered sector next, while reconstruction runs.
- `ply_viewer_node.py`: publishes a saved PLY on `/ur_perception/ply_preview`.
- `policy_visualizer_node.py`: composite head + wrist image with a detection heatmap on `/policy_visualizer/composite_image`.
- C++ PCL tools (`plane_segmentation`, `cluster_extraction`, `object_segmentation`, `normals_curvature_and_rsd_estimation`).

## Launch files

`perception.launch.py`, `reconstruct.launch.py`, `reconstruct_sweep.launch.py`, `view_reconstruction.launch.py`, `policy_visualizer.launch.py`.

## Key parameters

Detector (`config/detector_params.yaml`): `use_yolo`, `confidence_threshold`, `publish_planning_scene`, `min_depth_m`, `max_depth_m`, `depth_scale` (1.0 in Gazebo, 0.001 for a RealSense), `color_topic`, `depth_topic`, `camera_info_topic`, `target_colors`.

Reconstruction launch args: `camera_topic`, `colour`, `voxel_size`, `roi_radius`, `remove_table`, `outlier_filter`, `save_path`, `export_mesh`; sweep adds `dwell_sec`, `seg_sec`, `max_views`.

## Run

```bash
ros2 launch ur_perception perception.launch.py use_yolo:=false
ros2 launch ur_perception reconstruct_sweep.launch.py colour:=red
```

Needs the simulation (`ur_gazebo`) running for the camera topics.
