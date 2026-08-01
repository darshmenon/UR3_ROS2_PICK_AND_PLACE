#!/usr/bin/env python3
"""
Multi-object color sorting coordinator.

Reads /detected_objects, groups them by color, then picks each one
and places it in the matching color bin.  Bin positions are defined
in config/bins.yaml (or set as ROS params).

Usage:
    ros2 launch ur_sorting_demo sorting_demo.launch.py

Topics subscribed:
    /detected_objects  (ur_interfaces/DetectedObjectArray)

Services:
    /sorting/start   (std_srvs/Trigger) — begin a sorting cycle
    /sorting/stop    (std_srvs/Trigger) — abort current cycle

The node reuses MotionExecutor from ur_llm_planner so all pick/place
logic (IK seeding, Pilz PTP, gripper control) is identical.
"""

import math
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import String
from std_srvs.srv import Trigger
from ur_interfaces.msg import DetectedObjectArray

# ── default bin positions (x, y, z) in base_link frame ────────────────────────
# Override via ROS params:  ros2 param set /sorting_node bins.red.x 0.15

DEFAULT_BINS: dict[str, tuple[float, float, float]] = {
    "red":    (0.15,  0.30, 0.08),
    "green":  (0.35,  0.30, 0.08),
    "blue":   (0.50,  0.30, 0.08),
    "yellow": (0.15, -0.30, 0.08),
    "orange": (0.35, -0.30, 0.08),
}

SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)


class SortingNode(Node):
    def __init__(self):
        super().__init__("sorting_node")

        # Declare bin params
        for color, (x, y, z) in DEFAULT_BINS.items():
            self.declare_parameter(f"bins.{color}.x", x)
            self.declare_parameter(f"bins.{color}.y", y)
            self.declare_parameter(f"bins.{color}.z", z)

        self.declare_parameter("min_confidence", 0.5)
        self.declare_parameter("settle_time", 2.0)
        self.declare_parameter("max_objects_per_cycle", 10)

        self._min_confidence = self.get_parameter("min_confidence").value
        self._settle_time = self.get_parameter("settle_time").value
        self._max_objects = self.get_parameter("max_objects_per_cycle").value

        self._bins = self._load_bins()

        self._latest_objects: list = []
        self._objects_lock = threading.Lock()
        self._running = False

        self.create_subscription(
            DetectedObjectArray,
            "/detected_objects",
            self._objects_cb,
            SENSOR_QOS,
        )

        self._status_pub = self.create_publisher(String, "/sorting/status", 10)

        self.create_service(Trigger, "/sorting/start", self._start_cb)
        self.create_service(Trigger, "/sorting/stop", self._stop_cb)

        # Late-import MotionExecutor to avoid circular deps at import time
        from ur_llm_planner.motion_executor import MotionExecutor
        self._executor_obj = MotionExecutor(self)

        self.get_logger().info("SortingNode ready.  Call /sorting/start to begin.")

    # ── ROS callbacks ─────────────────────────────────────────────────────────

    def _objects_cb(self, msg: DetectedObjectArray):
        with self._objects_lock:
            self._latest_objects = list(msg.objects)

    def _start_cb(self, request, response):
        if self._running:
            response.success = False
            response.message = "Already running"
            return response
        threading.Thread(target=self._run_sort_cycle, daemon=True).start()
        response.success = True
        response.message = "Sorting started"
        return response

    def _stop_cb(self, request, response):
        self._running = False
        response.success = True
        response.message = "Stopping after current pick"
        return response

    # ── sorting logic ─────────────────────────────────────────────────────────

    def _run_sort_cycle(self):
        self._running = True
        self._publish_status("Starting sorting cycle")

        self.get_logger().info(f"Waiting {self._settle_time}s for perception to settle…")
        import time
        time.sleep(self._settle_time)

        with self._objects_lock:
            objects = list(self._latest_objects)

        filtered = [
            o for o in objects
            if o.confidence >= self._min_confidence and self._color_of(o) in self._bins
        ]

        if not filtered:
            msg = "No sortable objects detected (check confidence threshold and bin colors)"
            self.get_logger().warn(msg)
            self._publish_status(msg)
            self._running = False
            return

        # Sort by distance to arm so we pick nearest first (avoids reaching over objects)
        filtered.sort(key=lambda o: math.hypot(o.position.x, o.position.y))
        filtered = filtered[: self._max_objects]

        self.get_logger().info(f"Sorting {len(filtered)} object(s): {[o.id for o in filtered]}")

        if not self._executor_obj.wait_for_servers(timeout=10.0):
            self.get_logger().error("Motion servers not available — aborting.")
            self._publish_status("ERROR: motion servers unavailable")
            self._running = False
            return

        # Home first
        self._executor_obj.move_to_named_pose("arm", "home")

        succeeded = 0
        for obj in filtered:
            if not self._running:
                self.get_logger().info("Sort cycle aborted by user.")
                break

            color = self._color_of(obj)
            bin_x, bin_y, bin_z = self._bins[color]

            self._publish_status(f"Picking {obj.id} → {color} bin ({bin_x:.2f}, {bin_y:.2f})")
            self.get_logger().info(
                f"  Pick {obj.id} from ({obj.position.x:.3f}, {obj.position.y:.3f}, "
                f"{obj.position.z:.3f}) → bin at ({bin_x:.3f}, {bin_y:.3f}, {bin_z:.3f})"
            )

            tasks = [
                {
                    "action": "pick",
                    "object_id": obj.id,
                    "object_x": obj.position.x,
                    "object_y": obj.position.y,
                    "object_z": obj.position.z,
                },
                {
                    "action": "place",
                    "x": bin_x,
                    "y": bin_y,
                    "z": bin_z,
                },
            ]

            ok = self._executor_obj.execute_task_list(tasks)
            if ok:
                succeeded += 1
                self._publish_status(f"Placed {obj.id} in {color} bin ({succeeded} done)")
            else:
                self.get_logger().warn(f"Failed to sort {obj.id} — continuing with next.")

        self._executor_obj.move_to_named_pose("arm", "home")
        summary = f"Sort cycle complete: {succeeded}/{len(filtered)} placed"
        self.get_logger().info(summary)
        self._publish_status(summary)
        self._running = False

    # ── helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _color_of(obj) -> str:
        """Extract color keyword from object label or id (e.g. 'red_0' → 'red')."""
        for color in DEFAULT_BINS:
            if color in obj.label.lower() or color in obj.id.lower():
                return color
        return ""

    def _load_bins(self) -> dict[str, tuple[float, float, float]]:
        bins = {}
        for color in DEFAULT_BINS:
            x = self.get_parameter(f"bins.{color}.x").value
            y = self.get_parameter(f"bins.{color}.y").value
            z = self.get_parameter(f"bins.{color}.z").value
            bins[color] = (x, y, z)
            self.get_logger().info(f"  Bin [{color}]: ({x:.3f}, {y:.3f}, {z:.3f})")
        return bins

    def _publish_status(self, text: str):
        msg = String()
        msg.data = text
        self._status_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SortingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
