#!/usr/bin/env python3
"""
Fine-tune ACT on a LeRobotDataset exported by export_lerobot_dataset.py.

Thin wrapper around LeRobot's real `lerobot-train` CLI (draccus-style
flags, e.g. `--dataset.repo_id=... --policy.type=act`). No LeRobot core
changes needed -- ACT accepts `observation.state` as an arbitrary-length
vector, so any extra channels (e.g. estimated wrench, if later added to
the collector/exporter) would ride along automatically.

Must run under a Python 3.12 venv with LeRobot installed (e.g. .venv312 --
NOT the ROS2/py3.10 environment used by collector_node.py/train.py). This
script has no ROS2 or MuJoCo dependency itself.

Usage:
    .venv312/bin/python3 ur_data_collector/scripts/train_act.py \
      --dataset-root ./datasets/ur3_pickplace_v0 \
      --repo-id ur3-pickplace/pickplace-v0 \
      --output-dir ./outputs/act_v0

Confirm exact flag names against `.venv312/bin/lerobot-train --help` if
this repo's lerobot version has drifted from what's encoded here.
"""

import argparse
import os
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune ACT on an exported UR3 LeRobotDataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--dataset-root", default="./datasets/ur3_pickplace_v0")
    parser.add_argument("--repo-id", default="ur3-pickplace/pickplace-v0")
    parser.add_argument("--output-dir", default="./outputs/act_v0")
    parser.add_argument("--chunk-size", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--steps", type=int, default=20000)
    parser.add_argument("--save-freq", type=int, default=5000)
    parser.add_argument("--log-freq", type=int, default=200)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true", help="Print the command without running it")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    lerobot_train_bin = os.path.join(os.path.dirname(sys.executable), "lerobot-train")
    if not os.path.exists(lerobot_train_bin):
        print(f"ERROR: lerobot-train not found next to {sys.executable}.")
        print("Run this script with a Python 3.12 venv that has lerobot installed, e.g.:")
        print("  .venv312/bin/python3 ur_data_collector/scripts/train_act.py ...")
        return 2

    cmd = [
        lerobot_train_bin,
        f"--dataset.repo_id={args.repo_id}",
        f"--dataset.root={args.dataset_root}",
        "--policy.type=act",
        f"--policy.chunk_size={args.chunk_size}",
        f"--output_dir={args.output_dir}",
        f"--batch_size={args.batch_size}",
        f"--steps={args.steps}",
        f"--save_freq={args.save_freq}",
        f"--log_freq={args.log_freq}",
        f"--num_workers={args.num_workers}",
        "--policy.push_to_hub=false",      # policies.py: push_to_hub defaults True
        "--save_checkpoint_to_hub=false",  # fully local training, no HF Hub push
    ]

    print("Running:", " ".join(cmd))
    if args.dry_run:
        return 0

    subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
