#!/bin/bash
# Run VLM pick checks (4 colored objects in clutter, padded) and log PASS/FAIL to testing/_out/batch_pad6.log.
# Prerequisites: ROS 2 Humble installed, workspace built (install/setup.bash), no other gz sim running, free CPU and disk. VLM backend configured for testing/vlm_pick_check.py.
# Output goes to testing/_out/ (gitignored). Run from anywhere.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$REPO_ROOT/testing/_out"
cd "$REPO_ROOT"
source /opt/ros/humble/setup.bash >/dev/null 2>&1; source install/setup.bash >/dev/null 2>&1
OUT=testing/_out/batch_pad6.log; rm -f $OUT
for pair in "the green cube|green_box" "the red cylinder|red_cylinder" "the yellow cylinder|yellow_cylinder" "the blue cube|blue_box"; do
  q="${pair%%|*}"; e="${pair##*|}"
  python3 testing/vlm_pick_check.py --query "$q" --expect $e --domain 80 --record-dir testing/_out/recordings_clutter_pad6 > testing/_out/vlm_pad6_$e.out 2>&1
  echo "PAD6 $q -> $(grep -h 'PASS\|FAIL\|gave no\|MTC status' testing/_out/vlm_pad6_$e.out | head -1)" >> $OUT
done
echo DONE >> $OUT
