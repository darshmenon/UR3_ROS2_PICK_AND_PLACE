#!/bin/bash
# Launch Gazebo + live point cloud viewer in RViz
# Uses the live /camera_head/depth/color/points topic — no PCD files needed

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

export DISPLAY="${DISPLAY:-:1}"
export ROS_LOG_DIR="${ROS_LOG_DIR:-/tmp/roslogs}"
mkdir -p "$ROS_LOG_DIR"

echo "Launching Gazebo simulation..."
ros2 launch ur_gazebo ur.gazebo.launch.py \
    world_file:=pick_and_place_demo.world \
    use_rviz:=false &

echo "Waiting 20s for simulation to start..."
sleep 20

echo "Adjusting Gazebo GUI camera..."
gz service -s /gui/move_to/pose \
    --reqtype gz.msgs.GUICamera \
    --reptype gz.msgs.Boolean \
    --timeout 2000 \
    --req "pose: {position: {x: 1.36, y: -0.58, z: 0.95} orientation: {x: -0.26, y: 0.1, z: 0.89, w: 0.35}}" \
    || echo "Gazebo GUI camera move service not available yet; continuing without it."

echo "Launching live point cloud viewer in RViz..."
ros2 launch ur_gazebo point_cloud_viewer.launch.py

wait
