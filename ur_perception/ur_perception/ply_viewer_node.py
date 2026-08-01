#!/usr/bin/env python3
"""
ply_viewer_node.py — publish a saved ASCII PLY (from object_reconstructor_node's
save_path/export) as a latched PointCloud2, so it can be loaded into RViz after
the fact instead of only while reconstruction is actively running.

Parameters:
    ply_path   (str, required)         path to the ASCII PLY to load
    frame_id   (str, default base_link) frame to publish the cloud in
    topic      (str, default /ur_perception/ply_preview)
"""

import re

import numpy as np

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSProfile

from sensor_msgs.msg import PointCloud2, PointField
from std_msgs.msg import Header


def _load_ascii_ply(path: str) -> np.ndarray:
    with open(path, "r") as f:
        lines = f.readlines()

    n_vertex = None
    header_end = None
    for i, line in enumerate(lines):
        m = re.match(r"element vertex (\d+)", line.strip())
        if m:
            n_vertex = int(m.group(1))
        if line.strip() == "end_header":
            header_end = i
            break
    if n_vertex is None or header_end is None:
        raise ValueError(f"'{path}' does not look like an ASCII PLY (missing header)")

    cloud = np.zeros((n_vertex, 6), dtype=np.float32)
    for i in range(n_vertex):
        parts = lines[header_end + 1 + i].split()
        x, y, z, r, g, b = parts[:6]
        cloud[i] = [float(x), float(y), float(z), float(r), float(g), float(b)]
    return cloud


class PlyViewerNode(Node):
    def __init__(self):
        super().__init__("ply_viewer_node")

        self.declare_parameter("ply_path", "")
        self.declare_parameter("frame_id", "base_link")
        self.declare_parameter("topic", "/ur_perception/ply_preview")

        ply_path = str(self.get_parameter("ply_path").value)
        frame_id = str(self.get_parameter("frame_id").value)
        topic = str(self.get_parameter("topic").value)

        if not ply_path:
            self.get_logger().error(
                "ply_path parameter is empty — pass ply_path:=/path/to/file.ply"
            )
            return

        try:
            cloud = _load_ascii_ply(ply_path)
        except (OSError, ValueError) as exc:
            self.get_logger().error(f"Failed to load '{ply_path}': {exc}")
            return

        qos = QoSProfile(depth=1)
        qos.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        self._pub = self.create_publisher(PointCloud2, topic, qos)
        self._publish(cloud, frame_id)
        self.get_logger().info(
            f"Published {len(cloud)} points from '{ply_path}' on '{topic}' "
            f"(frame_id={frame_id}, latched) — add a PointCloud2 display on "
            f"that topic in RViz"
        )

    def _publish(self, cloud: np.ndarray, frame_id: str) -> None:
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = frame_id

        fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
            PointField(name="rgb", offset=12, datatype=PointField.FLOAT32, count=1),
        ]

        n = len(cloud)
        data = np.zeros((n, 4), dtype=np.float32)
        data[:, :3] = cloud[:, :3]
        r = cloud[:, 3].astype(np.uint32)
        g = cloud[:, 4].astype(np.uint32)
        b = cloud[:, 5].astype(np.uint32)
        rgb_packed = (r << 16) | (g << 8) | b
        data[:, 3] = rgb_packed.view(np.float32)

        msg = PointCloud2()
        msg.header = header
        msg.height = 1
        msg.width = n
        msg.fields = fields
        msg.is_bigendian = False
        msg.point_step = 16
        msg.row_step = 16 * n
        msg.is_dense = True
        msg.data = data.tobytes()
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = PlyViewerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
