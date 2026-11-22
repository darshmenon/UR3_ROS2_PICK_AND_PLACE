#!/bin/bash
# Sim queue only. Waits for the 2F-140 torsional run, then runs the next sims
# one at a time. Does not edit configs, rebuild, or commit. Parameter changes
# for a run are a throwaway YAML under testing/_out, passed as an overlay.
set -u
cd /home/asimov/UR3_ROS2_PICK_AND_PLACE
mkdir -p testing/_out
exec >> testing/_out/sim_queue.log 2>&1
echo "===== sim queue $(date -Is) ====="

# Match the python process itself. A shell that only mentions the script name must not hold the queue.
while pgrep -f '^python3 testing/benchmark_mtc.py' >/dev/null; do sleep 20; done
while pgrep -f 'gz sim.*colored_cylinder.world' >/dev/null; do sleep 5; done
echo "torsional run finished $(date -Is)"

python3 - <<'PY'
import csv
from pathlib import Path
p = Path("testing/_out/mtc_140_cyl5_tors.csv")
print("=== 2F-140 torsional vs 12/20 baseline ===")
if not p.exists():
    print("csv not written")
else:
    rows = [r for r in csv.DictReader(p.open()) if r.get("trial") and int(r["trial"]) > 0]
    def hit(r):
        try:
            return float(r["error_xy_m"]) <= 0.02
        except ValueError:
            return False
    print(f"torsional {sum(hit(r) for r in rows)}/{len(rows)} within 20 mm; baseline 12/20")
PY

set +u
source /opt/ros/humble/setup.bash
source install/setup.bash
set -u

cat > testing/_out/overlay_margin0.yaml <<'EOF'
mtc_node:
  ros__parameters:
    neighbor_object_margin: 0.0
EOF
cat > testing/_out/overlay_margin1cm.yaml <<'EOF'
mtc_node:
  ros__parameters:
    neighbor_object_margin: 0.01
EOF
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

run_mtc margin0 --grippers robotiq_2f_85 --objects clutter_cyl \
  --record-dir testing/_out/frames_margin0 --output testing/_out/mtc_margin0.csv \
  --mtc-overrides /home/asimov/UR3_ROS2_PICK_AND_PLACE/testing/_out/overlay_margin0.yaml

run_mtc margin1 --grippers robotiq_2f_85 --objects clutter_cyl \
  --record-dir testing/_out/frames_margin1 --output testing/_out/mtc_margin1.csv \
  --mtc-overrides /home/asimov/UR3_ROS2_PICK_AND_PLACE/testing/_out/overlay_margin1cm.yaml

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
echo "===== sim queue done $(date -Is) ====="
