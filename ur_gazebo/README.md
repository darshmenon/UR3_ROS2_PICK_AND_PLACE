# ur_gazebo

This package contains launch files and configurations for simulating the UR robot arm in Gazebo.

## Getting Started

To launch the robotic arm in Gazebo and RViz without MoveIt Task Constructor (MTC), you can run:

```bash
source install/setup.bash
ros2 launch ur_gazebo ur.gazebo.launch.py
```

This launch file will:
1. Start the Gazebo simulation environment
2. Spawn the UR3 arm with Robotiq 2F-85 gripper
3. Start the ROS 2 Control spawner for the arm and gripper controllers (~45s delay)
4. Launch RViz with the MoveIt motion planning panel
5. Start the ROS-Gazebo bridge (camera topics, clock, point cloud)

Note: MTC packages can be ignored using COLCON_IGNORE to speed up build time if not needed.

---

## Camera

An Intel RealSense D435 RGBD camera is mounted on a torso stand above the robot, tilted 55° downward to view the workspace.

Published ROS topics (via `ros_gz_image` bridge):

| Topic | Type | Description |
|---|---|---|
| `/camera_head/color/image_raw` | `sensor_msgs/Image` | Color stream (424×240, 10 Hz) |
| `/camera_head/depth/image_rect_raw` | `sensor_msgs/Image` | Depth stream |
| `/camera_head/depth/color/points` | `sensor_msgs/PointCloud2` | RGBD point cloud |
| `/camera_head/depth/camera_info` | `sensor_msgs/CameraInfo` | Camera intrinsics |

View the color feed:
```bash
ros2 run rqt_image_view rqt_image_view
# Select /camera_head/color/image_raw
```

Or add to RViz: **Add → By topic → /camera_head/color/image_raw → Image**

---

## Robot Control GUI

A standalone tkinter GUI with live camera feed and joint control:

```bash
source install/setup.bash
python3 ur_llm_planner/scripts/robot_gui.py
```

---

## Arm Mount Table

The default world (`colored_blocks.world`) spawns the arm on top of `mount_table`
(`ur_gazebo/models/mount_table/`), a wooden table model (1.5 × 0.8 m footprint,
top face at 1.015 m — legs are 1.0 m tall, topped with a 0.03 m-thick tabletop
centered at z=1.0, so the usable surface is 1.0 + 0.03/2 = 1.015 m).
The arm's `base_joint` is raised by the `table_height` argument so `base_link`
sits flush on that top face instead of the ground:

```bash
ros2 launch ur_gazebo ur.gazebo.launch.py table_height:=1.015 # default
ros2 launch ur_gazebo ur.gazebo.launch.py table_height:=0.0   # arm back on the ground
```

Getting this wrong by even a centimeter matters: if `table_height` is set
below the true top face (e.g. using the tabletop's *center* pose instead of
its top), the arm's base spawns embedded inside the solid table mesh. Bullet
resolves that interpenetration by shoving the overlapping bodies apart on the
very first physics step — visually the table looks like it "explodes" or the
arm goes flying. If that happens, the fix is almost always a height/offset
math error, not a physics engine problem.

`table_height` only shifts the arm's own mount — it does not move objects in the
world file. If you add a new world with the arm mounted on `mount_table`, place
every workspace object (blocks, drop zones, etc.) at `z + table_height` so their
position stays the same *relative to the arm's base_link* — grasp code such as
`ur_grasp/cylinder_grasp_detector.py` reasons entirely in the base_link frame, so
keeping that relative offset unchanged is what keeps grasp height thresholds valid.

### Adding a new model without git

Models here are downloaded straight from Gazebo Fuel over HTTP — no cloning,
no submodules. `gz fuel` ships with Gazebo:

```bash
# 1. Search Fuel for a model (or browse https://app.gazebosim.org)
curl -s "https://fuel.gazebosim.org/1.0/models?q=<keyword>" | python3 -m json.tool

# 2. Download it (fetches to ~/.gz/fuel/..., HTTP only)
gz fuel download -u https://fuel.gazebosim.org/1.0/<owner>/models/<name>

# 3. Copy just the files you need into this package (rename the folder/model
#    if it could collide with an existing one, e.g. "Table" -> "mount_table")
cp -r ~/.gz/fuel/fuel.gazebosim.org/<owner>/models/<name>/<version> \
      ur_gazebo/models/<your_model_name>

# 4. In model.sdf: set <model name="..."> to match the folder name, and point
#    any texture/mesh <uri> at model://<your_model_name>/... so it resolves
#    locally instead of re-fetching from fuel.gazebosim.org at runtime.

# 5. Reference it from a world file:
#    <include>
#      <name>your_instance_name</name>
#      <uri>model://your_model_name</uri>
#      <pose>x y z 0 0 0</pose>
#    </include>
```

`GZ_SIM_RESOURCE_PATH` already includes `ur_gazebo/models` (see
`set_env_vars_resources` in `ur.gazebo.launch.py`), so any model dropped in
that folder resolves via `model://` without further setup.

To mount the arm on top of a new table-like model, don't just copy its
tabletop `<pose>` z value straight into `table_height` — that pose is almost
always the geometry's **center**, not its top face. Find the top surface with:

```
table_height = tabletop_pose_z + (tabletop_thickness / 2)
```

e.g. `mount_table`'s tabletop is `<pose>0 0 1.0 ...>` with a `0.03` box
height, so top = `1.0 + 0.03/2` = `1.015` (the current default). Using the
bare pose value (`1.0`) embeds the arm's base a bit inside the table, and
Bullet reacts to that overlap by flinging everything apart on the first step.
Add the model's `<include>` at the same x/y as the arm (usually `0 0 0`) so
the base lands centered on the surface.

---

## Controller Timing

Controllers are spawned with delays to wait for Gazebo physics to stabilise:

| Controller | Delay |
|---|---|
| `joint_state_broadcaster` | 35 s |
| `arm_controller` | 40 s |
| `gripper_controller` | 45 s |

Wait for `"You can start planning now!"` in the logs before sending motion commands.
