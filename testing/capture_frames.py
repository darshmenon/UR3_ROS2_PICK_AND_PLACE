#!/usr/bin/env python3
"""Save camera frames from a running (headless) sim as PNGs, so a run can be inspected.

    python3 testing/capture_frames.py --topic /camera_head/color/image_raw --out frames --period 0.7

Stop with Ctrl-C (or --seconds). Frames are named by wall-clock time.
"""
import argparse
import os
import time
from pathlib import Path

import cv2
import rclpy
import numpy as np
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="/camera_head/color/image_raw")
    ap.add_argument("--out", default="frames")
    ap.add_argument("--period", type=float, default=1.0, help="seconds between saved frames")
    ap.add_argument("--seconds", type=float, default=0.0, help="stop after this long (0 = until Ctrl-C)")
    ap.add_argument("--domain", type=int, default=int(os.environ.get("ROS_DOMAIN_ID", 0)))
    args = ap.parse_args()
    os.environ["ROS_DOMAIN_ID"] = str(args.domain)

    rclpy.init()
    node = Node("capture_frames")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    state = {"last": 0.0, "n": 0}
    t_end = time.time() + args.seconds if args.seconds else None

    def cb(msg):
        now = time.time()
        if now - state["last"] < args.period:
            return
        state["last"] = now
        # Decoded by hand: cv_bridge is built against NumPy 1.x and crashes here.
        img = np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.width, -1)
        if msg.encoding == "rgb8":
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(out / f"{now:.2f}.png"), img)
        state["n"] += 1

    qos = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT, history=HistoryPolicy.KEEP_LAST, depth=1)
    node.create_subscription(Image, args.topic, cb, qos)
    try:
        while rclpy.ok() and (t_end is None or time.time() < t_end):
            rclpy.spin_once(node, timeout_sec=0.2)
    except KeyboardInterrupt:
        pass
    print(f"saved {state['n']} frames to {out}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
