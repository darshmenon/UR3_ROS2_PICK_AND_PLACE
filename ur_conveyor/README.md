# ur_conveyor

Simulated conveyor belt. `conveyor_node` spawns coloured boxes at the belt entry (x about 0.90) and moves them to the pick zone by publishing pose updates to the Gazebo `/world/conveyor_sorting/set_pose` topic. A box that is not picked within the hold time is despawned.

## Interface

- Publishes `/conveyor/object_ready` (`"box_N colour"`) and `/conveyor/status`.
- Subscribes `/conveyor/picked`.
- Services `/conveyor/start` and `/conveyor/stop` (Trigger).
- Params: `spawn_interval_s` (6.0), `belt_speed` (0.03 m/s), `pick_zone_x` (0.35), `belt_y`, `belt_z`, `hold_timeout_s` (8.0), `world_name`.

## Run

```bash
ros2 launch ur_conveyor conveyor.launch.py spawn_interval_s:=6.0 belt_speed:=0.03
ros2 service call /conveyor/start std_srvs/srv/Trigger {}
```

The conveyor world must be loaded in Gazebo first. `ur_sorting_demo` full_sorting_demo.launch.py brings the pieces up together.
