#!/bin/bash
# Headless launch script — isolates UR3 on ROS_DOMAIN_ID=77
# to avoid cross-contamination with other ROS2 sessions on domain 0.
set -a
source /opt/ros/humble/setup.bash
source "$(cd "$(dirname "$0")" && pwd)/install/setup.bash"
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-77}
export GZ_VERSION=harmonic
set +a

BRAIN=${1:-llm}
MODEL_PATH=${2:-}

echo "[UR3] Launching on ROS_DOMAIN_ID=$ROS_DOMAIN_ID  brain=$BRAIN"

if [ "$BRAIN" = "rl" ] && [ -z "$MODEL_PATH" ]; then
    echo "[UR3] ERROR: brain=rl requires a model path as second argument"
    exit 1
fi

exec ros2 launch ur_gazebo full_demo.launch.py \
    brain:="$BRAIN" \
    ${MODEL_PATH:+model_path:="$MODEL_PATH"}
