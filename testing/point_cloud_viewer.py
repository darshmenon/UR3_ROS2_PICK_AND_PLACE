#!/usr/bin/env python3
"""
point_cloud_viewer.py  —  live 3-D point cloud from /camera_head/depth/color/points
Uses matplotlib (no PCL / open3d required).

Usage
-----
source install/setup.bash
python3 testing/point_cloud_viewer.py             # random-downsample to 2000 pts
python3 testing/point_cloud_viewer.py --max 5000  # more points (slower refresh)
python3 testing/point_cloud_viewer.py --save      # save a .ply each refresh

Keys in the window: q = quit, r = reset view, s = save snapshot
"""

import argparse
import struct
import sys
import threading
import time

import matplotlib
matplotlib.use("TkAgg")          # headless fallback: 'Agg'
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2 as pc2


# ── tunables ────────────────────────────────────────────────────────────────
TOPIC   = "/camera_head/depth/color/points"
REFRESH = 0.5   # seconds between plot updates
# ──────────────────────────────────────────────────────────────────────────


class PointCloudViewer(Node):
    def __init__(self, max_pts: int = 2000, save: bool = False):
        super().__init__("point_cloud_viewer")
        self.max_pts = max_pts
        self.save    = save
        self._lock   = threading.Lock()
        self._cloud  = None        # latest (N, 6) array: xyz + rgb
        self._frame  = 0

        self.create_subscription(
            PointCloud2, TOPIC, self._cb, 10
        )
        self.get_logger().info(f"Subscribed to {TOPIC}")

    # ── ROS callback ────────────────────────────────────────────────────────
    def _cb(self, msg: PointCloud2) -> None:
        pts = list(pc2.read_points(msg, field_names=("x", "y", "z", "rgb"),
                                   skip_nans=True))
        if not pts:
            return

        arr = np.array(pts, dtype=np.float32)   # (N, 4)
        # decode packed RGB float → uint8 r, g, b
        rgb_packed = arr[:, 3].view(np.uint32)
        r = ((rgb_packed >> 16) & 0xFF).astype(np.float32) / 255.0
        g = ((rgb_packed >>  8) & 0xFF).astype(np.float32) / 255.0
        b = ((rgb_packed      ) & 0xFF).astype(np.float32) / 255.0

        # random downsample
        n = len(arr)
        if n > self.max_pts:
            idx = np.random.choice(n, self.max_pts, replace=False)
            arr = arr[idx]
            r, g, b = r[idx], g[idx], b[idx]

        cloud = np.column_stack([arr[:, :3], r, g, b])   # (N, 6)

        with self._lock:
            self._cloud = cloud
            self._frame += 1

    # ── matplotlib loop (call from main thread) ──────────────────────────────
    def spin_plot(self) -> None:
        plt.ion()
        fig = plt.figure("PointCloud — /camera_head/depth/color/points",
                         figsize=(9, 7))
        ax  = fig.add_subplot(111, projection="3d")
        scatter = None
        last_frame = -1

        def on_key(event):
            if event.key in ("q", "escape"):
                plt.close("all")

        fig.canvas.mpl_connect("key_press_event", on_key)

        try:
            while plt.fignum_exists(fig.number):
                with self._lock:
                    cloud = self._cloud
                    frame = self._frame

                if cloud is not None and frame != last_frame:
                    last_frame = frame
                    ax.cla()
                    ax.set_title(f"frame {frame}  |  {len(cloud)} pts  (q to quit)",
                                 fontsize=9)
                    ax.set_xlabel("X (m)"); ax.set_ylabel("Y (m)"); ax.set_zlabel("Z (m)")
                    ax.scatter(cloud[:, 0], cloud[:, 1], cloud[:, 2],
                               c=cloud[:, 3:6], s=1, linewidths=0)

                    if self.save:
                        fname = f"/tmp/pointcloud_{frame:04d}.ply"
                        _save_ply(fname, cloud)
                        print(f"saved {fname}")

                plt.pause(REFRESH)

        except KeyboardInterrupt:
            pass
        finally:
            plt.close("all")


def _save_ply(path: str, cloud: np.ndarray) -> None:
    """Write a minimal ASCII PLY file (xyz + rgb)."""
    n = len(cloud)
    with open(path, "w") as f:
        f.write(
            "ply\nformat ascii 1.0\n"
            f"element vertex {n}\n"
            "property float x\nproperty float y\nproperty float z\n"
            "property uchar red\nproperty uchar green\nproperty uchar blue\n"
            "end_header\n"
        )
        for pt in cloud:
            r, g, b = int(pt[3]*255), int(pt[4]*255), int(pt[5]*255)
            f.write(f"{pt[0]:.4f} {pt[1]:.4f} {pt[2]:.4f} {r} {g} {b}\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max",  type=int,  default=2000, help="max points per frame")
    ap.add_argument("--save", action="store_true",      help="save .ply snapshots to /tmp")
    args = ap.parse_args()

    rclpy.init()
    node = PointCloudViewer(max_pts=args.max, save=args.save)

    # spin ROS in background thread
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    print(f"Waiting for first cloud on {TOPIC} ...")
    node.spin_plot()

    rclpy.shutdown()
    spin_thread.join(timeout=2.0)


if __name__ == "__main__":
    main()
