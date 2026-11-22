# ur_bt_planner

Behaviour-tree task execution (py_trees) for pick and place.

## Nodes

- `bt_planner_node`: hierarchical pick-place tree with retry and fallback; each leaf (`bt_leaves.py`) wraps a `MotionExecutor` call from `ur_llm_planner`. Services `/bt/run_pick_place` and `/bt/stop`; status on `/bt/status`. Params `pick_x/y/z`, `place_x/y/z`, `tick_rate_hz`, `use_compliant_grasp`.
- `mtc_retry_node.py`: retry wrapper around `ur_mtc_pick_place_demo`'s `run_pick_place` service. Services `/mtc_bt/run` and `/mtc_bt/stop`; status on `/mtc_bt/status`. Params `max_attempts` (5), `mtc_service_name`, `tick_rate_hz`, `call_timeout` (320 s).

## Launch files

`bt_planner.launch.py`, `mtc_retry.launch.py` (also starts the MTC node), `dual_mtc_retry.launch.py` (left and right namespaces).

## Run

```bash
ros2 launch ur_bt_planner mtc_retry.launch.py auto_run_on_startup:=false
ros2 service call /mtc_bt/run std_srvs/srv/Trigger {}
```

Dual arm: `ros2 launch ur_bt_planner dual_mtc_retry.launch.py`, then call `/left/mtc_bt/run` and `/right/mtc_bt/run`.
