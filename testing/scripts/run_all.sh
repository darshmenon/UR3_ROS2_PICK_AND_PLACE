#!/bin/bash
# Pipeline: YCB VLM picks, then grasp data collection (4 gripper/object sets into ~/grasp_data), then train held/quality models.
# Prerequisites: ROS 2 Humble installed, workspace built (install/setup.bash), no other gz sim running, free CPU and disk. VLM backend, YCB models, ~/grasp_data writable, over 2GB free disk.
# Output goes to testing/_out/ (gitignored). Run from anywhere.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$REPO_ROOT/testing/_out"
cd "$REPO_ROOT"
source /opt/ros/humble/setup.bash >/dev/null 2>&1
source install/setup.bash >/dev/null 2>&1
LOG=testing/_out/overnight2.log
log() { echo "[$(date +%H:%M:%S)] $*" >> $LOG; }
free_gb() { df --output=avail -BG /home | tail -1 | tr -dc '0-9'; }
YCB="ycb_005_tomato_soup_can ycb_013_apple ycb_011_banana ycb_025_mug ycb_010_potted_meat_can"

for pair in "the apple|ycb_013_apple" "the banana|ycb_011_banana" "the mug|ycb_025_mug" "the can of spam|ycb_010_potted_meat_can"; do
  q="${pair%%|*}"; e="${pair##*|}"
  log "YCB pick: $q"
  python3 testing/vlm_pick_check.py --query "$q" --expect $e --world ycb_objects.world --models $YCB --domain 80 \
      --record-dir testing/_out/recordings_ycb > testing/_out/vlm_ycb_$e.out 2>&1
  cp logs/vlm_pick_check.log testing/_out/vlmnode_ycb_$e.log
  cp logs/bench_robotiq_2f_85_ycb_objects.world.log testing/_out/sim_ycb_$e.log
  log "  -> $(grep -h 'PASS\|FAIL\|gave no' testing/_out/vlm_ycb_$e.out | head -1)"
done

collect() {   # gripper object trials outdir
  if [ "$(free_gb)" -lt 2 ]; then log "SKIP collect $1 $2: disk low"; return; fi
  log "START collect $1 $2 x$3"
  python3 testing/collect_grasp_data.py --gripper $1 --object $2 --trials $3 --domain 91 --random-yaw \
      --out ~/grasp_data/$4 >> testing/_out/collect_$4.log 2>&1
  log "END collect $1 $2 rc=$? rows=$(wc -l < ~/grasp_data/$4/data.jsonl 2>/dev/null)"
}
collect robotiq_2f_85  cylinder_5cm 200 2f85_cyl_yaw
collect onrobot_rg2    cylinder_5cm 200 rg2_cyl_yaw
collect robotiq_2f_85  tall_box     150 2f85_tall_yaw
collect robotiq_2f_140 cylinder_5cm 150 2f140_cyl_yaw

log "training held/quality on all data"
python3 testing/train_grasp_model.py --task held    --data ~/grasp_data/*/ --out ~/grasp_data/held4.pt    >> testing/_out/train_held4.log 2>&1
log "held rc=$?"
python3 testing/train_grasp_model.py --task quality --data ~/grasp_data/*/ --out ~/grasp_data/quality4.pt >> testing/_out/train_quality4.log 2>&1
log "quality rc=$?"
log "ALL DONE"
