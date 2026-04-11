#!/bin/bash
# Launch Gazebo + MoveIt + MTC pick-and-place demo

cleanup() {
    echo "Cleaning up..."
    sleep 2.0
    pkill -9 -f "ros2|gazebo|gz|rviz2|robot_state_publisher|joint_state_publisher|move_group"
}

trap 'cleanup' SIGINT SIGTERM

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../../../../setup.bash" ]; then
    # Installed script path: <ws>/install/<pkg>/share/<pkg>/scripts
    source "$SCRIPT_DIR/../../../../setup.bash"
elif [ -f "$SCRIPT_DIR/../../install/setup.bash" ]; then
    # Source tree path: <ws>/src-or-root/<pkg>/scripts
    source "$SCRIPT_DIR/../../install/setup.bash"
else
    echo "Could not locate a workspace setup.bash from $SCRIPT_DIR"
    exit 1
fi

export ROS_LOG_DIR="${ROS_LOG_DIR:-/tmp/roslogs}"
mkdir -p "$ROS_LOG_DIR"

if [ -z "${DISPLAY:-}" ]; then
    echo "DISPLAY is not set. Gazebo GUI needs an active desktop session."
    echo "Set DISPLAY first, or run headless by passing use_gazebo_gui:=false manually."
    exit 1
fi

echo "Launching Gazebo simulation..."
ros2 launch ur_gazebo ur.gazebo.launch.py \
    world_file:=pick_and_place_demo.world \
    use_rviz:=false \
    use_move_group:=false \
    use_gazebo_gui:=true &

sleep 40

echo "Adjusting Gazebo GUI camera..."
gz service -s /gui/move_to/pose \
    --reqtype gz.msgs.GUICamera \
    --reptype gz.msgs.Boolean \
    --timeout 2000 \
    --req "pose: {position: {x: 1.36, y: -0.58, z: 0.95} orientation: {x: -0.26, y: 0.1, z: 0.89, w: 0.35}}" \
    || echo "Gazebo GUI camera move service not available yet; continuing without it."

echo "Launching MoveIt move_group..."
ros2 launch moveit_config move_group.launch.py \
    use_rviz:=false \
    rviz_config_file:=mtc_demos.rviz \
    rviz_config_package:=ur_mtc_pick_place_demo &

sleep 15

echo "Launching planning scene server..."
ros2 launch ur_mtc_pick_place_demo get_planning_scene_server.launch.py &

sleep 40

echo "Launching Pick and Place demo..."
ros2 launch ur_mtc_pick_place_demo pick_place_demo.launch.py

wait
