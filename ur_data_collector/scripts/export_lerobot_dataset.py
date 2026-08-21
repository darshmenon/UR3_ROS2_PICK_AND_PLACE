#!/usr/bin/env python3
"""
Export UR3 HDF5 demonstrations to a local LeRobotDataset.

Input files are produced by ur_data_collector/collector_node.py. The output
dataset can be used with LeRobot policies such as ACT, Diffusion Policy, and
SmolVLA.

Example:
    python3 ur_data_collector/scripts/export_lerobot_dataset.py \
      --input-dir ~/ur3_demos \
      --output-root ~/lerobot_ur3_pickplace \
      --repo-id local/ur3_pickplace \
      --task "pick the red block and place it in the bin"
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from pathlib import Path

try:
    import h5py
except ImportError:
    h5py = None

try:
    import numpy as np
except ImportError:
    np = None


ARM_JOINT_NAMES = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
GRIPPER_JOINT_NAME = "finger_joint"


def _add_lerobot_to_path(path: str) -> None:
    root = Path(os.path.expanduser(path)).resolve()
    src = root / "src"
    if src.exists():
        sys.path.insert(0, str(src))


def _estimate_fps(timestamps: np.ndarray, fallback: int) -> int:
    if len(timestamps) < 2:
        return fallback
    deltas = np.diff(timestamps.astype(np.float64))
    deltas = deltas[deltas > 1e-6]
    if len(deltas) == 0:
        return fallback
    return max(1, int(round(1.0 / float(np.median(deltas)))))


def _feature_names(names: list[str]) -> list[list[str]]:
    return [names]


def _make_features(height: int, width: int, use_videos: bool) -> dict:
    image_dtype = "video" if use_videos else "image"
    state_names = ARM_JOINT_NAMES + [GRIPPER_JOINT_NAME]
    return {
        "observation.images.rgb": {
            "dtype": image_dtype,
            "shape": (height, width, 3),
            "names": ["height", "width", "channel"],
        },
        "observation.state": {
            "dtype": "float32",
            "shape": (7,),
            "names": _feature_names(state_names),
        },
        "action": {
            "dtype": "float32",
            "shape": (7,),
            "names": _feature_names(state_names),
        },
    }


def _episode_files(input_dir: str) -> list[str]:
    pattern = os.path.join(os.path.expanduser(input_dir), "*.h5")
    return sorted(glob.glob(pattern))


def _read_episode(path: str) -> dict:
    with h5py.File(path, "r") as f:
        rgb = f["rgb_images"][:]
        joints = f["joint_positions"][:].astype(np.float32)
        gripper = f["gripper_positions"][:].astype(np.float32)
        actions = f["actions"][:].astype(np.float32)
        timestamps = f["timestamps"][:] if "timestamps" in f else np.arange(len(actions), dtype=np.float64)
    if gripper.ndim == 1:
        gripper = gripper[:, None]
    state = np.concatenate([joints, gripper[:, :1]], axis=1).astype(np.float32)
    return {
        "rgb": rgb,
        "state": state,
        "action": actions,
        "timestamps": timestamps,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert UR3 HDF5 demos into a LeRobotDataset.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input-dir", default="~/ur3_demos")
    parser.add_argument("--output-root", default="~/lerobot_ur3_pickplace")
    parser.add_argument("--repo-id", default="local/ur3_pickplace")
    parser.add_argument("--task", default="pick the object and place it in the target zone")
    parser.add_argument("--robot-type", default="ur3_robotiq_2f85")
    parser.add_argument("--fps", type=int, default=0, help="0 means infer from timestamps")
    parser.add_argument("--lerobot-root", default="~/lerobot", help="Path to cloned LeRobot repo")
    parser.add_argument("--images", action="store_true", help="Store image files instead of MP4 videos")
    parser.add_argument("--limit-episodes", type=int, default=0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if h5py is None or np is None:
        missing = []
        if h5py is None:
            missing.append("h5py")
        if np is None:
            missing.append("numpy")
        print(f"ERROR: missing Python package(s): {', '.join(missing)}")
        print("Install them in the environment used to run this exporter.")
        print("Example:")
        print("  pip install h5py numpy")
        return 2

    _add_lerobot_to_path(args.lerobot_root)

    try:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
    except ImportError as exc:
        print(f"ERROR: could not import LeRobotDataset: {exc}")
        print("Install LeRobot in a separate Python 3.12 venv, then rerun this exporter.")
        print("Example:")
        print("  cd ~/lerobot")
        print("  python3.12 -m venv .venv")
        print("  source .venv/bin/activate")
        print('  pip install -e ".[dataset]" h5py')
        print("  cd ~/UR3_ROS2_PICK_AND_PLACE")
        print("  python3.12 ur_data_collector/scripts/export_lerobot_dataset.py --input-dir ~/ur3_demos")
        return 2

    files = _episode_files(args.input_dir)
    if args.limit_episodes > 0:
        files = files[: args.limit_episodes]
    if not files:
        print(f"ERROR: no .h5 episodes found in {os.path.expanduser(args.input_dir)}")
        return 1

    first = _read_episode(files[0])
    height, width = first["rgb"].shape[1], first["rgb"].shape[2]
    fps = args.fps or _estimate_fps(first["timestamps"], fallback=5)
    use_videos = not args.images

    features = _make_features(height, width, use_videos=use_videos)
    dataset = LeRobotDataset.create(
        repo_id=args.repo_id,
        fps=fps,
        root=os.path.expanduser(args.output_root),
        robot_type=args.robot_type,
        features=features,
        use_videos=use_videos,
        image_writer_threads=4,
    )

    total_frames = 0
    for episode_index, path in enumerate(files):
        ep = first if episode_index == 0 else _read_episode(path)
        n = min(len(ep["rgb"]), len(ep["state"]), len(ep["action"]))
        if n == 0:
            print(f"Skipping empty episode: {path}")
            continue

        for i in range(n):
            dataset.add_frame(
                {
                    "observation.images.rgb": ep["rgb"][i],
                    "observation.state": ep["state"][i],
                    "action": ep["action"][i],
                    "task": args.task,
                }
            )
        dataset.save_episode()
        total_frames += n
        print(f"episode {episode_index:04d}: {Path(path).name} -> {n} frames")

    dataset.finalize()
    print(f"\nExported {len(files)} episode(s), {total_frames} frame(s)")
    print(f"LeRobot dataset root: {os.path.expanduser(args.output_root)}")
    print(f"Repo id: {args.repo_id}")
    print(f"FPS: {fps}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
