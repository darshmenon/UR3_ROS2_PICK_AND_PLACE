#!/bin/bash
# Compiles the MTC package only after the live sim has exited.
# The installed mtc_node is a symlink into the build tree, so a build
# during a trial replaces the binary that trial is running.
set -u
cd /home/asimov/UR3_ROS2_PICK_AND_PLACE
mkdir -p testing/_out
exec >> testing/_out/rebuild_when_idle.log 2>&1
echo "===== rebuild waiting $(date -Is) ====="

while pgrep -f 'testing/benchmark_mtc.py' >/dev/null; do sleep 30; done
while pgrep -f 'testing/scripts/run_resume.sh' >/dev/null; do sleep 20; done
while pgrep -f 'testing/scripts/run_rest.sh' >/dev/null; do sleep 20; done
while pgrep -f 'testing/vlm_pick_check.py' >/dev/null; do sleep 20; done
while pgrep -f 'gz sim.*UR3_ROS2_PICK_AND_PLACE' >/dev/null; do sleep 10; done
while pgrep -f 'UR3_ROS2_PICK_AND_PLACE/.*/mtc_node' >/dev/null; do sleep 10; done
echo "idle $(date -Is)"

set +u
source /opt/ros/humble/setup.bash
source install/setup.bash
set -u
set -e
colcon build --packages-select ur_mtc_pick_place_demo --cmake-args -DCMAKE_BUILD_TYPE=Release
echo "build ok $(date -Is)"
