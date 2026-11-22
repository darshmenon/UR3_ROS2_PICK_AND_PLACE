#!/bin/bash
# Starts only after the margin/padding/VLM queue has exited. One sim at a time.
# Rebuilds the MTC package (the live binary must not be replaced while that queue runs),
# then runs the trials that need the new parameters. Does not commit.
set -u
cd /home/asimov/UR3_ROS2_PICK_AND_PLACE
mkdir -p testing/_out
exec >> testing/_out/after_queue.log 2>&1
echo "===== after queue waiting $(date -Is) ====="

while pgrep -f '[b]enchmark_mtc.py' >/dev/null; do sleep 30; done
while pgrep -f '[r]un_remaining.sh' >/dev/null; do sleep 10; done
while pgrep -f '[g]z sim' >/dev/null; do sleep 5; done
while pgrep -x '[m]tc_node' >/dev/null || pgrep -f '/mtc_node' >/dev/null; do sleep 15; done
echo "queue idle $(date -Is)"

set +u
source /opt/ros/humble/setup.bash
source install/setup.bash
set -u

echo "=== build mtc $(date -Is) ==="
set -e
colcon build --packages-select ur_mtc_pick_place_demo ur_perception --cmake-args -DCMAKE_BUILD_TYPE=Release
set +e
echo "build ok $(date -Is)"

set +u
source install/setup.bash
set -u

if [ -x build/ur_mtc_pick_place_demo/test_cloud_filters ]; then
  echo "=== cloud filter gtest ==="
  ./build/ur_mtc_pick_place_demo/test_cloud_filters || true
fi

cat > testing/_out/overlay_retreat.yaml <<'EOF'
mtc_node:
  ros__parameters:
    retreat_velocity_scaling: 0.1
EOF
cat > testing/_out/overlay_pilz.yaml <<'EOF'
mtc_node:
  ros__parameters:
    linear_planner: pilz_lin
EOF
cat > testing/_out/overlay_split.yaml <<'EOF'
mtc_node:
  ros__parameters:
    task_part: split
EOF

run_mtc() {
  local name="$1"
  shift
  echo "=== $name $(date -Is) ==="
  python3 testing/benchmark_mtc.py --attempts 2 --domain 91 --trials 10 \
    --record-period 0.25 --record-tail 14 "$@"
  echo "=== $name done $(date -Is) ==="
}

run_mtc retreat --grippers robotiq_2f_85 --objects cylinder_5cm \
  --record-dir testing/_out/frames_retreat --output testing/_out/mtc_retreat.csv \
  --mtc-overrides /home/asimov/UR3_ROS2_PICK_AND_PLACE/testing/_out/overlay_retreat.yaml

run_mtc split --grippers robotiq_2f_85 --objects cylinder_5cm \
  --record-dir testing/_out/frames_split --output testing/_out/mtc_split.csv \
  --mtc-overrides /home/asimov/UR3_ROS2_PICK_AND_PLACE/testing/_out/overlay_split.yaml

echo "=== pilz_lin probe $(date -Is) ==="
python3 testing/benchmark_mtc.py --attempts 1 --domain 91 --trials 2 \
  --record-period 0.25 --record-tail 14 \
  --grippers robotiq_2f_85 --objects cylinder_5cm \
  --record-dir testing/_out/frames_pilz --output testing/_out/mtc_pilz.csv \
  --mtc-overrides /home/asimov/UR3_ROS2_PICK_AND_PLACE/testing/_out/overlay_pilz.yaml || true

run_mtc rg6 --grippers onrobot_rg6 --objects cylinder_5cm \
  --record-dir testing/_out/frames_rg6 --output testing/_out/mtc_rg6_cyl.csv

echo "===== after queue done $(date -Is) ====="
