# ur_llm_planner

Natural-language control of the UR3. A local Ollama LLM turns a text command into a task plan, and `MotionExecutor` runs it through MoveIt (`move_group`) and the gripper action.

## Nodes

- `llm_planner_node.py`: subscribes to `/llm_planner/command` (`std_msgs/String`), `/detected_objects`, `/vlm/target_object_id`, and `/vlm/target_pose`. The VLM selection is moved to the front of the object list before the LLM plans. Named poses: `home`, `ready`.
- `motion_executor.py` / `ollama_client.py`: library modules; `MotionExecutor` is also used by `ur_bt_planner` and `ur_sorting_demo`.
- `keyboard_teleop.py`: joint and Cartesian keyboard jogging, gripper open/close (press H for keys).
- `robot_gui.py`: tkinter GUI with arm control and camera feed.

## Launch files

`llm_planner.launch.py` (args `ollama_model`, `ollama_base_url`, `auto_demo`, `auto_demo_command`), `keyboard_teleop.launch.py`. Defaults are in `config/planner_params.yaml`.

## Run

```bash
ollama serve   # and pull the model
ros2 launch ur_llm_planner llm_planner.launch.py ollama_model:=mistral:7b
ros2 topic pub --once /llm_planner/command std_msgs/msg/String "{data: 'pick up the red object and place it to the left'}"
```

Needs the simulation, MoveIt and `ur_perception` running.
