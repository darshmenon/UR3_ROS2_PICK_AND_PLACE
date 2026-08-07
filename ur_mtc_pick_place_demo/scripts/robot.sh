#!/bin/bash
# Launch Gazebo + MoveIt + MTC pick-and-place demo
# Usage: bash robot.sh [gripper]
#   gripper: robotiq_2f_85 (default) | robotiq_2f_140 | onrobot_rg2 | onrobot_rg6
#
# Isolates this demo on ROS_DOMAIN_ID=113 by default so leftover stacks on
# other domains (42/53/91/99/…) cannot poison DDS discovery.

GRIPPER="${1:-robotiq_2f_85}"
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-113}"
export ROS_LOCALHOST_ONLY="${ROS_LOCALHOST_ONLY:-1}"

LAUNCH_PIDS=()

cleanup() {
    echo "Cleaning up UR3 MTC demo (domain ${ROS_DOMAIN_ID})..."
    for pid in "${LAUNCH_PIDS[@]:-}"; do
        kill "$pid" 2>/dev/null || true
    done
    sleep 1
    # Scoped — do not pkill every ros2 process on the machine.
    pkill -f "ur.gazebo.launch.py" 2>/dev/null || true
    pkill -f "pick_place_demo.launch.py" 2>/dev/null || true
    pkill -f "get_planning_scene_server.launch.py" 2>/dev/null || true
    pkill -f "lib/ur_mtc_pick_place_demo/" 2>/dev/null || true
    pkill -f "pick_and_place_demo.world" 2>/dev/null || true
    # move_group started by ur_gazebo; only kill if our domain's child remains
    pkill -f "moveit_ros_move_group/move_group" 2>/dev/null || true
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

USE_GUI="${USE_GAZEBO_GUI:-true}"
if [ "$USE_GUI" = "true" ] && [ -z "${DISPLAY:-}" ]; then
    echo "DISPLAY is not set. Gazebo GUI needs an active desktop session."
    echo "Set DISPLAY, or run headless: USE_GAZEBO_GUI=false bash robot.sh"
    exit 1
fi

echo "[UR3 MTC] ROS_DOMAIN_ID=$ROS_DOMAIN_ID ROS_LOCALHOST_ONLY=$ROS_LOCALHOST_ONLY gripper=$GRIPPER"

echo "Launching Gazebo + MoveIt move_group (gripper: $GRIPPER)..."
# use_move_group:=true launches move_group inside ur_gazebo — more stable than a
# separate process because it starts before the GUI-induced sim-clock reset at ~50s.
ros2 launch ur_gazebo ur.gazebo.launch.py \
    world_file:=pick_and_place_demo.world \
    gripper:="$GRIPPER" \
    use_rviz:=false \
    use_move_group:=true \
    use_gazebo_gui:="$USE_GUI" &
LAUNCH_PIDS+=($!)

echo "Waiting for move_group / controllers / camera..."
READY=0
for i in $(seq 1 90); do
    HAS_SCENE=0
    HAS_ARM=0
    HAS_GRIP=0
    HAS_POINTS=0
    if timeout 2 ros2 service list 2>/dev/null | grep -q "/get_planning_scene"; then
        HAS_SCENE=1
    fi
    if timeout 2 ros2 action list 2>/dev/null | grep -q "/arm_controller/follow_joint_trajectory"; then
        HAS_ARM=1
    fi
    # GripperActionController — without this, execute fails immediately with CONTROL_FAILED (-4)
    if timeout 2 ros2 action list 2>/dev/null | grep -q "/gripper_controller/gripper_cmd"; then
        HAS_GRIP=1
    fi
    # topic hz can hang under some sandboxes; treat points as optional soft check
    if timeout --signal=KILL 3 ros2 topic hz /camera_head/depth/color/points 2>&1 | grep -q average; then
        HAS_POINTS=1
    fi
    if [ "$HAS_SCENE" -eq 1 ] && [ "$HAS_ARM" -eq 1 ] && [ "$HAS_GRIP" -eq 1 ]; then
        READY=1
        echo "Ready at attempt $i (scene+arm+gripper; points=$HAS_POINTS)."
        break
    fi
    echo "  wait $i: scene=$HAS_SCENE arm=$HAS_ARM grip=$HAS_GRIP points=$HAS_POINTS"
    sleep 2
done
if [ "$READY" -ne 1 ]; then
    echo "ERROR: timed out waiting for move_group readiness on domain $ROS_DOMAIN_ID"
    cleanup
    exit 1
fi

if [ "$USE_GUI" = "true" ]; then
    sleep 2
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
    LAUNCH_PIDS+=($!)
    sleep 5
fi

echo "Launching planning scene server..."
ros2 launch ur_mtc_pick_place_demo get_planning_scene_server.launch.py &
LAUNCH_PIDS+=($!)
sleep 5

echo "Launching Pick and Place demo..."
ros2 launch ur_mtc_pick_place_demo pick_place_demo.launch.py \
    gripper:="$GRIPPER"

wait
