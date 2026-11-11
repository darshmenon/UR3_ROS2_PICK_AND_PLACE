# UR3 peg-in-hole with Cartesian impedance control

Peg-in-hole in headless Gazebo and in MuJoCo, with a Cartesian impedance controller, force-triggered spiral search, camera frames and contact-force plots.

![UR3 inserting the peg after a spiral search](../assets/gifs/peg_in_hole_ur3_spiral.gif)

## Gazebo (ros2_control, effort mode)

```bash
colcon build --packages-select moveit_config ur_description ur_gazebo ur_force_control
python3 ur_force_control/scripts/record_peg_in_hole.py --out assets/gifs/peg_in_hole_ur3.gif --offset-x 0.0004
python3 ur_force_control/scripts/record_peg_in_hole.py --out assets/gifs/peg_in_hole_ur3_spiral.gif --offset-x 0.004 --search
```

The script starts the sim (server only, `--headless-rendering`), moves the UR3 above the hole with `arm_controller`, switches to
`forward_command_controller_effort`, runs `cartesian_impedance_controller` and `peg_in_hole_task.py`, films the `peg_close` camera, and
writes `<out>.gif`, `<out>.csv` and `<out>_forces.png`.

| Piece | File |
|---|---|
| Controller `tau = J^T [K (x_des - x) - D v] + g(q)` (Pinocchio) | `src/cartesian_impedance_controller.cpp` |
| Descent, jam detection, spiral search, CSV log | `ur_force_control/peg_in_hole_task.py` |
| World: square hole, 0.5 mm clearance per side, 30 mm deep, two cameras | `ur_gazebo/worlds/peg_in_hole.world` |
| Rigid peg tool (`gripper:=peg`), 500 Hz controller config | `ur_description/urdf/ur_macro.xacro`, `moveit_config/config/ros2_controllers_peg.yaml` |

Controller topics: `~/target_pose`, `~/stiffness` (6 values, change impedance on the fly), `~/tip_pose`, service `~/hold_current_pose`.

## MuJoCo

`ur_force_control/peg_in_hole_env.py` (UR3) and `scripts/peg_in_hole_impedance.py`, `scripts/peg_in_hole_spiral_search.py` (force plots for several stiffnesses and offsets).

## Things to know

- **Switch controllers once per sim session.** After `arm_controller` -> `forward_command_controller_effort` the Gazebo joints stay in force mode, so switching back does not move the arm. Restart the sim to retest.
- **The controller loop must be fast.** The UR3 wrists have about 1e-3 kg m^2 of joint inertia and no armature. At the default 100 Hz the controller is unstable; the `peg` config runs at 500 Hz and the damping defaults are low on purpose.
- **Poses are in the URDF root frame**, which includes the table height: the hole top face is at z = 1.135.
- **"Contact force" in the Gazebo plots is the commanded impedance spring force** `K (x_des - x)`, not a measured contact force.
- **Gazebo contact is softer than the model suggests.** The hole has 0.5 mm clearance per side, but in Gazebo a peg 1.5 mm off-center still goes in, and at 4 mm offset it jams on the rim. Treat the numbers as qualitative.

Results from the three recorded runs (K = 800 N/m, 10 mm/s):

| Run | Offset | Result | Peak axial / lateral |
|---|---|---|---|
| plain descent | 0.4 mm | inserts | 0.7 N / 0.3 N |
| plain descent | 4 mm | jams on the rim | 21.6 N / 3.2 N |
| spiral search | 4 mm | inserts after about 5 s of search | 3.6 N / 12.9 N |
