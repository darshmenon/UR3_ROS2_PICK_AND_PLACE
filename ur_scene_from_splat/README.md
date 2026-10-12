# ur_scene_from_splat

Gaussian-splat point cloud -> Gazebo scene: a support surface plus one rigid object per cluster, each with mesh, collision, mass and inertia. Scenes are plain `world.sdf` + assets, so any robot the launch file spawns can use them.

```bash
python3 -m ur_scene_from_splat.splat2scene --npz cafe_points_final.npz \
    --roi -1.3 -2.15 -0.85 0.9 -0.9 0.45 --out scenes/cafe_counter [--decompose]
ros2 launch ur_scene_from_splat scene.launch.py world:=$PWD/scenes/cafe_counter/world.sdf
```

Input `.npz` (xyz/rgb/opacity) comes from rosnav's `gs_splat_to_pointcloud.py`; for real video use `~/gaussian-splat-world-recon` (COLMAP + splatfacto) first.

- Visual and collision default to the convex hull of the cluster (robust to holes on unseen sides); `--decompose` uses CoACD (`pip install coacd`).
- Clusters touching `--max-height` are dropped as background (`--keep-tall` to keep).
- Mass = `--density` x hull volume x `--fill` (a guess, not measured).
- Scale/up-axis are taken from the splat as-is.
- Dexterous hands are not included: Allegro/Shadow/LEAP exist only as MJCF in `~/mujoco_menagerie`, no Gazebo URDF yet.
