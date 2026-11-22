#!/bin/bash
# Run VLM pick checks on 4 YCB objects, then 4 colored clutter objects; summary in testing/_out/batch1114.log.
# Prerequisites: ROS 2 Humble installed, workspace built (install/setup.bash), no other gz sim running, free CPU and disk. YCB models generated (testing/make_ycb_models.py); VLM backend configured.
# Output goes to testing/_out/ (gitignored). Run from anywhere.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$REPO_ROOT/testing/_out"
cd "$REPO_ROOT"
source /opt/ros/humble/setup.bash >/dev/null 2>&1
source install/setup.bash >/dev/null 2>&1
YCB="ycb_005_tomato_soup_can ycb_013_apple ycb_011_banana ycb_025_mug ycb_010_potted_meat_can"
OUT=testing/_out/batch1114.log
for pair in "the apple|ycb_013_apple" "the banana|ycb_011_banana" "the mug|ycb_025_mug" "the can of spam|ycb_010_potted_meat_can"; do
  q="${pair%%|*}"; e="${pair##*|}"
  python3 testing/vlm_pick_check.py --query "$q" --expect $e --world ycb_objects.world --models $YCB --domain 80 \
      --record-dir testing/_out/recordings_ycb > testing/_out/vlm_ycb_$e.out 2>&1
  cp logs/bench_robotiq_2f_85_ycb_objects.world.log testing/_out/sim_ycb_$e.log 2>/dev/null
  echo "YCB $q -> $(grep -h 'PASS\|FAIL\|gave no' testing/_out/vlm_ycb_$e.out | head -1)" >> $OUT
done
for pair in "the green cube|green_box" "the red cylinder|red_cylinder" "the blue cube|blue_box" "the yellow cylinder|yellow_cylinder"; do
  q="${pair%%|*}"; e="${pair##*|}"
  python3 testing/vlm_pick_check.py --query "$q" --expect $e --domain 80 \
      --record-dir testing/_out/recordings_clutter > testing/_out/vlm_clutter_$e.out 2>&1
  echo "CLUTTER $q -> $(grep -h 'PASS\|FAIL\|gave no' testing/_out/vlm_clutter_$e.out | head -1)" >> $OUT
done
echo DONE >> $OUT
