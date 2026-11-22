# ur_sorting_demo

Colour sorting. `sorting_node` reads `/detected_objects`, groups objects by colour, and picks each into the matching bin using `MotionExecutor` from `ur_llm_planner`.

## Interface

- Services `sorting/start` and `sorting/stop` (Trigger, relative so they can be namespaced, for example `/left/sorting/start`); status on `sorting/status`.
- Params: bin positions `bins.<colour>.x/y/z`, `max_objects_per_cycle`, `min_confidence`, `settle_time`, `prefix`, and workspace split (`enable_workspace_split`, `split_axis`, `split_value`, `split_keep_positive`).
- Bin defaults are in the node; `config/bins_left.yaml` and `config/bins_right.yaml` are for the dual-arm setup.

## Launch files

- `sorting_demo.launch.py`: the node alone (args include `min_confidence`, `settle_time`, `auto_start`, `namespace`).
- `dual_sorting_demo.launch.py`: left and right instances.
- `full_sorting_demo.launch.py`: conveyor world, perception and sorting together (args `spawn_interval_s`, `belt_speed`, `min_confidence`, `settle_time`, `auto_start`).

## Run

```bash
ros2 launch ur_sorting_demo sorting_demo.launch.py
ros2 service call /sorting/start std_srvs/srv/Trigger {}
```

Needs the simulation, MoveIt and `ur_perception` running.
