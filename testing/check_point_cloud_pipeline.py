#!/usr/bin/env python3
"""
Quick point-cloud pipeline smoke test for the UR MTC demo.

What it checks:
1. A PointCloud2 message arrives on /camera_head/depth/color/points
2. The get_planning_scene service is reachable
3. The service returns a support surface / target object summary

Usage:
    source /opt/ros/humble/setup.bash
    source install/setup.bash
    python3 testing/check_point_cloud_pipeline.py
    python3 testing/check_point_cloud_pipeline.py --shape box --dims 0.04 0.04 0.08
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import List

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import PointCloud2
from ur_interfaces.srv import GetPlanningScene


POINT_CLOUD_TOPIC = "/camera_head/depth/color/points"
PLANNING_SCENE_SERVICE = "/get_planning_scene_ur"


class PointCloudPipelineChecker(Node):
    def __init__(self, cloud_timeout_s: float) -> None:
        super().__init__("point_cloud_pipeline_checker")
        self._cloud_timeout_s = cloud_timeout_s
        self._latest_cloud: PointCloud2 | None = None
        self._cloud_received_at: float | None = None

        self.create_subscription(
            PointCloud2,
            POINT_CLOUD_TOPIC,
            self._point_cloud_callback,
            10,
        )

        self._service_client = self.create_client(
            GetPlanningScene, PLANNING_SCENE_SERVICE
        )

    def _point_cloud_callback(self, msg: PointCloud2) -> None:
        self._latest_cloud = msg
        self._cloud_received_at = time.time()

    def wait_for_cloud(self) -> PointCloud2 | None:
        deadline = time.time() + self._cloud_timeout_s
        while time.time() < deadline and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.2)
            if self._latest_cloud is not None:
                return self._latest_cloud
        return None

    def call_planning_scene_service(
        self, target_shape: str, target_dimensions: List[float], service_timeout_s: float
    ) -> GetPlanningScene.Response | None:
        if not self._service_client.wait_for_service(timeout_sec=service_timeout_s):
            return None

        request = GetPlanningScene.Request()
        request.target_shape = target_shape
        request.target_dimensions = target_dimensions

        future = self._service_client.call_async(request)
        deadline = time.time() + service_timeout_s

        while time.time() < deadline and rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.2)
            if future.done():
                return future.result()

        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test the point-cloud and segmentation pipeline."
    )
    parser.add_argument(
        "--shape",
        default="cylinder",
        help="Target shape passed to the planning scene service.",
    )
    parser.add_argument(
        "--dims",
        type=float,
        nargs="*",
        default=[0.35, 0.0125],
        help="Target dimensions passed to the planning scene service.",
    )
    parser.add_argument(
        "--cloud-timeout",
        type=float,
        default=10.0,
        help="Seconds to wait for a point cloud.",
    )
    parser.add_argument(
        "--service-timeout",
        type=float,
        default=20.0,
        help="Seconds to wait for the planning-scene service and response.",
    )
    return parser.parse_args()


def print_cloud_summary(cloud: PointCloud2) -> None:
    print("Point cloud check: OK")
    print(f"  topic: {POINT_CLOUD_TOPIC}")
    print(f"  frame_id: {cloud.header.frame_id}")
    print(f"  width x height: {cloud.width} x {cloud.height}")
    print(f"  point_step: {cloud.point_step}")
    print(f"  row_step: {cloud.row_step}")
    print(f"  is_dense: {cloud.is_dense}")


def print_service_summary(response: GetPlanningScene.Response) -> None:
    collision_objects = response.scene_world.collision_objects

    print("Planning scene service check: OK")
    print(f"  success: {response.success}")
    print(f"  support_surface_id: {response.support_surface_id or '<none>'}")
    print(f"  target_object_id: {response.target_object_id or '<none>'}")
    print(f"  collision_objects: {len(collision_objects)}")
    print(
        f"  returned cloud size: {response.full_cloud.width} x {response.full_cloud.height}"
    )
    print(
        f"  returned image size: {response.rgb_image.width} x {response.rgb_image.height}"
    )

    if collision_objects:
        print("  objects:")
        for obj in collision_objects:
            primitive_types = [primitive.type for primitive in obj.primitives]
            print(f"    - {obj.id}: primitives={primitive_types}")

    if not response.success:
        print("Segmentation status: service responded but target matching failed.")
        print("This usually means the support plane was found, but no object matched the requested shape/dimensions.")


def main() -> int:
    args = parse_args()
    rclpy.init()

    node = PointCloudPipelineChecker(cloud_timeout_s=args.cloud_timeout)

    try:
        cloud = node.wait_for_cloud()
        if cloud is None:
            print("Point cloud check: FAILED")
            print(f"  no message received on {POINT_CLOUD_TOPIC} within {args.cloud_timeout:.1f}s")
            return 1

        print_cloud_summary(cloud)

        response = node.call_planning_scene_service(
            args.shape, args.dims, args.service_timeout
        )
        if response is None:
            print("Planning scene service check: FAILED")
            print(
                f"  service {PLANNING_SCENE_SERVICE} was unavailable or timed out after {args.service_timeout:.1f}s"
            )
            return 2

        print_service_summary(response)
        return 0 if response.success else 3
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    sys.exit(main())
