#!/bin/bash
# Launch Gazebo + MoveIt + MTC pick-and-place demo
# Usage: bash robot.sh [gripper]
#   gripper: robotiq_2f_85 (default) | robotiq_2f_140 | onrobot_rg2 | onrobot_rg6

GRIPPER="${1:-robotiq_2f_85}"

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

# Required for Gazebo Harmonic + local gz_ros2_control build
export GZ_VERSION=harmonic
LOCAL_GZ_LIB="$(ros2 pkg prefix gz_ros2_control)/lib"
export GZ_SIM_SYSTEM_PLUGIN_PATH="${LOCAL_GZ_LIB}:${GZ_SIM_SYSTEM_PLUGIN_PATH:-}"

export ROS_LOG_DIR="${ROS_LOG_DIR:-/tmp/roslogs}"
mkdir -p "$ROS_LOG_DIR"

# Remove stale FastRTPS SHM segments left by previous runs — they cause
# "Action client not connected" by blocking DDS action-server discovery.
find /dev/shm -name 'fastrtps_*' -delete 2>/dev/null || true
find /dev/shm -name 'sem.fastrtps_*' -delete 2>/dev/null || true

if [ -z "${DISPLAY:-}" ]; then
    echo "DISPLAY is not set. Gazebo GUI needs an active desktop session."
    echo "Set DISPLAY first, or run headless by passing use_gazebo_gui:=false manually."
    exit 1
fi

echo "Launching Gazebo + MoveIt move_group (gripper: $GRIPPER)..."
# use_move_group:=true launches move_group inside ur_gazebo — more stable than a
# separate process because it starts before the GUI-induced sim-clock reset at ~50s.
ros2 launch ur_gazebo ur.gazebo.launch.py \
    world_file:=pick_and_place_demo.world \
    gripper:="$GRIPPER" \
    use_rviz:=false \
    use_move_group:=true \
    use_gazebo_gui:=true &

echo "Waiting for move_group to be ready..."
until ros2 service list 2>/dev/null | grep -q "/get_planning_scene"; do
    sleep 2
done
echo "move_group ready."

sleep 5

echo "Adjusting Gazebo GUI camera..."
gz service -s /gui/move_to/pose \
    --reqtype gz.msgs.GUICamera \
    --reptype gz.msgs.Boolean \
    --timeout 2000 \
    --req "pose: {position: {x: 1.36, y: -0.58, z: 0.95} orientation: {x: -0.26, y: 0.1, z: 0.89, w: 0.35}}" \
    || echo "Gazebo GUI camera move service not available yet; continuing without it."

echo "Launching RViz..."
# use_move_group:=false — move_group is already running from ur_gazebo launch above
ros2 launch moveit_config move_group.launch.py \
    gripper:="$GRIPPER" \
    use_rviz:=true \
    use_move_group:=false \
    rviz_config_file:=mtc_demos.rviz \
    rviz_config_package:=ur_mtc_pick_place_demo &

sleep 5

echo "Launching planning scene server..."
ros2 launch ur_mtc_pick_place_demo get_planning_scene_server.launch.py &

sleep 5

echo "Launching Pick and Place demo..."
ros2 launch ur_mtc_pick_place_demo pick_place_demo.launch.py \
    gripper:="$GRIPPER"

wait
