#!/usr/bin/env python3
"""Launch a world headless and save one frame from its showcase camera.

    python3 testing/snapshot_world.py --world ycb_objects.world --out assets/ycb_objects.png
"""
import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import benchmark_grippers as bench  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--gripper", default="robotiq_2f_85")
    ap.add_argument("--domain", type=int, default=81)
    ap.add_argument("--settle", type=float, default=40.0)
    args = ap.parse_args()
    os.environ["ROS_DOMAIN_ID"] = str(args.domain)
    (bench.REPO / "logs").mkdir(exist_ok=True)
    sim = bridge = None
    try:
        sim, _ = bench.launch_sim(args.gripper, args.world, args.domain, args.settle)
        env = dict(os.environ, GZ_VERSION="harmonic")
        bridge = subprocess.Popen(
            ["bash", "-c", f"source /opt/ros/humble/setup.bash && source {bench.REPO}/install/setup.bash && "
                           "exec ros2 run ros_gz_image image_bridge /showcase_cam/image"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, preexec_fn=os.setsid)
        time.sleep(8)
        import cv2
        import numpy as np
        import rclpy
        from sensor_msgs.msg import Image
        rclpy.init()
        node = rclpy.create_node("snapshot_world")
        got = {}
        node.create_subscription(Image, "/showcase_cam/image", lambda m: got.__setitem__("m", m), 1)
        end = time.time() + 30
        while "m" not in got and time.time() < end:
            rclpy.spin_once(node, timeout_sec=0.2)
        for _ in range(10):
            rclpy.spin_once(node, timeout_sec=0.1)
        m = got.get("m")
        if m is None:
            sys.exit("no image from /showcase_cam/image")
        img = np.frombuffer(m.data, np.uint8).reshape(m.height, m.width, -1)
        if m.encoding == "rgb8":
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(args.out, img)
        print("saved", args.out, img.shape)
        rclpy.shutdown()
    finally:
        if bridge is not None:
            try:
                os.killpg(os.getpgid(bridge.pid), signal.SIGINT)
            except Exception:  # noqa: BLE001
                pass
        bench.stop_sim([sim])


if __name__ == "__main__":
    main()
