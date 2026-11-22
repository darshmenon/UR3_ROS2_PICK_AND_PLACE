#!/bin/bash
# Collect successful MTC picks (robotiq_2f_85; 4 objects x 15 trials) as joint-state demos in ~/ur3_rl_demos/mtc.
# Prerequisites: ROS 2 Humble installed, workspace built (install/setup.bash), no other gz sim running, free CPU and disk. ~/ur3_rl_demos writable.
# Output goes to testing/_out/ (gitignored). Run from anywhere.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$REPO_ROOT/testing/_out"
cd "$REPO_ROOT"
source /opt/ros/humble/setup.bash; source install/setup.bash
python3 testing/benchmark_mtc.py --grippers robotiq_2f_85 --objects cube_5cm cylinder_5cm cylinder_4cm tall_box \
  --trials 15 --attempts 3 --demo-dir ~/ur3_rl_demos/mtc --output testing/_out/mtc_demos.csv
