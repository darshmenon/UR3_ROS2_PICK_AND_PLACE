#!/usr/bin/env python3
"""
Live camera feed viewer from Gazebo simulation.

Shows the robot's camera view with OpenCV.
Optionally overlays HSV color detection for blue/green blocks.

Usage:
    source install/setup.bash
    python3 testing/camera_view.py           # plain view
    python3 testing/camera_view.py --detect  # with block detection overlay
"""

import sys
import threading

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import Image

DETECT = "--detect" in sys.argv

# HSV ranges for block detection
HSV_RANGES = {
    "blue":  [(100, 80, 50), (130, 255, 255)],
    "green": [(40, 60, 40),  (85, 255, 255)],
}

bridge = CvBridge()
latest_frame = None
frame_lock = threading.Lock()


def detect_blocks(frame_bgr):
    """Draw bounding boxes around blue and green blocks."""
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    colors_bgr = {"blue": (220, 100, 0), "green": (0, 180, 0)}

    for name, (lo, hi) in HSV_RANGES.items():
        mask = cv2.inRange(hsv, np.array(lo), np.array(hi))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  np.ones((5, 5), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv2.contourArea(cnt) < 400:
                continue
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), colors_bgr[name], 2)
            cv2.putText(frame_bgr, name, (x, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors_bgr[name], 2)

    return frame_bgr


class CameraNode(Node):
    def __init__(self):
        super().__init__("camera_view")
        self.create_subscription(
            Image,
            "/camera_head/color/image_raw",
            self._image_cb,
            10,
        )
        self.get_logger().info("Subscribed to /camera_head/color/image_raw")

    def _image_cb(self, msg: Image):
        global latest_frame
        try:
            frame = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
            with frame_lock:
                latest_frame = frame.copy()
        except Exception as e:
            self.get_logger().error(f"cv_bridge error: {e}")


def main():
    rclpy.init()
    node = CameraNode()
    ex = SingleThreadedExecutor()
    ex.add_node(node)
    spin_thread = threading.Thread(target=ex.spin, daemon=True)
    spin_thread.start()

    print("Press  q  to quit,  d  to toggle detection overlay")
    detect = DETECT

    while True:
        with frame_lock:
            frame = latest_frame.copy() if latest_frame is not None else None

        if frame is None:
            # Show waiting screen
            blank = np.zeros((240, 424, 3), dtype=np.uint8)
            cv2.putText(blank, "Waiting for camera...", (40, 120),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (180, 180, 180), 2)
            cv2.imshow("UR3 Camera", blank)
        else:
            display = frame.copy()
            if detect:
                display = detect_blocks(display)
            label = "detection ON" if detect else "press 'd' for detection"
            cv2.putText(display, label, (8, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
            cv2.imshow("UR3 Camera", display)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q') or key == 27:
            break
        if key == ord('d'):
            detect = not detect
            print(f"Detection: {'ON' if detect else 'OFF'}")

    cv2.destroyAllWindows()
    ex.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
