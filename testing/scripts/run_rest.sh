#!/bin/bash
# Waits for run_after_queue.sh, then finishes the padding and VLM/YCB cells
# the earlier queue never completed. One sim at a time. Does not commit.
set -u
cd /home/asimov/UR3_ROS2_PICK_AND_PLACE
mkdir -p testing/_out
exec >> testing/_out/rest_queue.log 2>&1
echo "===== rest queue waiting $(date -Is) ====="

while pgrep -f 'testing/scripts/run_after_queue.sh' >/dev/null; do sleep 30; done
while pgrep -f 'testing/benchmark_mtc.py' >/dev/null; do sleep 30; done
while pgrep -f 'testing/vlm_pick_check.py' >/dev/null; do sleep 20; done
while pgrep -f 'gz sim' >/dev/null; do sleep 10; done
echo "previous queue idle $(date -Is)"

set +u
source /opt/ros/humble/setup.bash
source install/setup.bash
set -u

cat > testing/_out/overlay_pad6.yaml <<'EOF'
mtc_node:
  ros__parameters:
    planning_robot_padding: 0.006
EOF

run_mtc() {
  local name="$1"
  shift
  echo "=== $name $(date -Is) ==="
  python3 testing/benchmark_mtc.py --attempts 2 --domain 91 --trials 10 \
    --record-period 0.25 --record-tail 14 "$@"
  echo "=== $name done $(date -Is) ==="
}

for g in robotiq_2f_140 onrobot_rg2 robotiq_hande dh_ag95; do
  run_mtc "pad6_${g}" --grippers "$g" --objects clutter_cyl \
    --record-dir "testing/_out/frames_pad6_${g}" --output "testing/_out/mtc_pad6_${g}.csv" \
    --mtc-overrides /home/asimov/UR3_ROS2_PICK_AND_PLACE/testing/_out/overlay_pad6.yaml
done

echo "=== VLM and YCB $(date -Is) ==="
YCB="ycb_005_tomato_soup_can ycb_013_apple ycb_011_banana ycb_025_mug ycb_010_potted_meat_can"
for pair in "the apple|ycb_013_apple" "the banana|ycb_011_banana" "the mug|ycb_025_mug" "the can of spam|ycb_010_potted_meat_can"; do
  q="${pair%%|*}"; e="${pair##*|}"
  python3 testing/vlm_pick_check.py --query "$q" --expect "$e" --world ycb_objects.world --models $YCB --domain 91 \
    --record-dir testing/_out/recordings_ycb > "testing/_out/vlm_ycb_${e}.out" 2>&1 || true
  echo "YCB $q -> $(grep -h -E 'PASS|FAIL|gave no' "testing/_out/vlm_ycb_${e}.out" | head -1)"
done
for pair in "the green cube|green_box" "the red cylinder|red_cylinder" "the blue cube|blue_box" "the yellow cylinder|yellow_cylinder"; do
  q="${pair%%|*}"; e="${pair##*|}"
  python3 testing/vlm_pick_check.py --query "$q" --expect "$e" --domain 91 \
    --record-dir testing/_out/recordings_clutter > "testing/_out/vlm_clutter_${e}.out" 2>&1 || true
  echo "CLUTTER $q -> $(grep -h -E 'PASS|FAIL|gave no' "testing/_out/vlm_clutter_${e}.out" | head -1)"
done
echo "===== rest queue done $(date -Is) ====="
