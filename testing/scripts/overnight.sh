#!/bin/bash
# Sequential unattended MTC gripper benchmarks (2f_85/rg2/rg6 cube, 2f_140 cylinder), domain 91.
# Prerequisites: ROS 2 Humble installed, workspace built (install/setup.bash), no other gz sim running, free CPU and disk.
# Output goes to testing/_out/ (gitignored). Run from anywhere.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$REPO_ROOT/testing/_out"
cd "$REPO_ROOT"
source /opt/ros/humble/setup.bash >/dev/null 2>&1
source install/setup.bash >/dev/null 2>&1
O=testing/_out
run() { # name, args...
  n=$1; shift
  echo "[$(date +%T)] START $n" >> $O/overnight.log
  timeout 3000 python3 testing/benchmark_mtc.py "$@" --domain 91 --output $O/$n.csv --record-dir $O/frames_$n > $O/$n.log 2>&1
  echo "[$(date +%T)] END $n rc=$?" >> $O/overnight.log
  sleep 20
}
run mtc_85_cube   --grippers robotiq_2f_85 --objects cube_5cm --trials 3
run mtc_rg2_cube  --grippers onrobot_rg2 --objects cube_5cm --trials 3
run mtc_rg6_cube  --grippers onrobot_rg6 --objects cube_5cm --trials 3
run mtc_140_cyl5  --grippers robotiq_2f_140 --objects cylinder_5cm --trials 5
echo "[$(date +%T)] ALL DONE" >> $O/overnight.log
