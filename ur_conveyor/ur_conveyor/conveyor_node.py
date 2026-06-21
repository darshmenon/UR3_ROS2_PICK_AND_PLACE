#!/usr/bin/env python3
"""
Conveyor belt simulation node.

Periodically spawns colored boxes at the belt entry (x≈0.90) and moves
them toward the UR3 pick zone (x≈0.35) by publishing pose updates via
the Gazebo UserCommands `/world/conveyor_sorting/set_pose` topic.

When a box reaches the pick zone it publishes its presence on
/conveyor/object_ready (std_msgs/String: "{id} {color}") so the sorting
or BT node can pick it up.  After a configurable hold time, if no pick
occurred, the box is despawned to avoid clutter.

Topics published:
    /conveyor/object_ready  (std_msgs/String) — "box_N red"
    /conveyor/status        (std_msgs/String) — human-readable status

Services:
    /conveyor/start  (std_srvs/Trigger) — start belt
    /conveyor/stop   (std_srvs/Trigger) — stop belt

Parameters:
    spawn_interval_s  (float, 6.0)  — seconds between spawns
    belt_speed        (float, 0.06) — m/s movement speed
    pick_zone_x       (float, 0.35) — X position of pick zone
    belt_y            (float, 0.0)  — Y centre of belt
    belt_z            (float, 0.07) — Z height of boxes on belt (belt top + half box)
    hold_timeout_s    (float, 8.0)  — seconds to wait before despawning unpicked box
"""

import random
import subprocess
import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import Trigger

COLORS = {
    "red":    (0.9, 0.1, 0.1),
    "green":  (0.1, 0.8, 0.1),
    "blue":   (0.1, 0.1, 0.9),
    "yellow": (0.9, 0.8, 0.0),
    "orange": (0.9, 0.5, 0.0),
}

ENTRY_X = 0.88   # belt far end (entry)
BOX_HALF = 0.025  # half-size of box (0.05 m cube)


def _make_box_sdf(name: str, x: float, y: float, z: float, color: str) -> str:
    r, g, b = COLORS.get(color, (0.5, 0.5, 0.5))
    return f"""<?xml version="1.0"?>
<sdf version="1.7">
  <model name="{name}">
    <pose>{x} {y} {z} 0 0 0</pose>
    <link name="link">
      <inertial>
        <mass>0.08</mass>
        <inertia>
          <ixx>0.00008</ixx><ixy>0</ixy><ixz>0</ixz>
          <iyy>0.00008</iyy><iyz>0</iyz>
          <izz>0.00008</izz>
        </inertia>
      </inertial>
      <collision name="collision">
        <geometry><box><size>0.05 0.05 0.05</size></box></geometry>
        <surface>
          <friction>
            <ode><mu>1.5</mu><mu2>1.5</mu2></ode>
          </friction>
        </surface>
      </collision>
      <visual name="visual">
        <geometry><box><size>0.05 0.05 0.05</size></box></geometry>
        <material>
          <ambient>{r} {g} {b} 1</ambient>
          <diffuse>{r} {g} {b} 1</diffuse>
          <specular>0.2 0.2 0.2 1</specular>
        </material>
      </visual>
    </link>
  </model>
</sdf>"""


class ConveyorNode(Node):
    def __init__(self):
        super().__init__("conveyor_node")

        self.declare_parameter("spawn_interval_s", 6.0)
        self.declare_parameter("belt_speed",       0.06)
        self.declare_parameter("pick_zone_x",      0.35)
        self.declare_parameter("belt_y",           0.0)
        self.declare_parameter("belt_z",           0.075)
        self.declare_parameter("hold_timeout_s",   8.0)
        self.declare_parameter("world_name",       "default")

        self._spawn_interval = self.get_parameter("spawn_interval_s").value
        self._belt_speed     = self.get_parameter("belt_speed").value
        self._pick_x         = self.get_parameter("pick_zone_x").value
        self._belt_y         = self.get_parameter("belt_y").value
        self._belt_z         = self.get_parameter("belt_z").value
        self._hold_timeout   = self.get_parameter("hold_timeout_s").value
        self._world          = self.get_parameter("world_name").value

        self._running = False
        self._counter = 0
        # {name: {"color": str, "x": float, "picked": bool}}
        self._boxes: dict = {}
        self._boxes_lock = threading.Lock()

        self._ready_pub  = self.create_publisher(String, "/conveyor/object_ready", 10)
        self._status_pub = self.create_publisher(String, "/conveyor/status", 10)

        self.create_service(Trigger, "/conveyor/start", self._start_cb)
        self.create_service(Trigger, "/conveyor/stop",  self._stop_cb)

        # /conveyor/picked: external node calls this to tell us a box was picked
        self.create_subscription(String, "/conveyor/picked", self._picked_cb, 10)

        self.get_logger().info(
            f"ConveyorNode ready. world='{self._world}' "
            f"speed={self._belt_speed} m/s  interval={self._spawn_interval}s"
        )

    def _start_cb(self, request, response):
        if self._running:
            response.success = False
            response.message = "Already running"
            return response
        self._running = True
        threading.Thread(target=self._belt_loop, daemon=True).start()
        response.success = True
        response.message = "Conveyor started"
        return response

    def _stop_cb(self, request, response):
        self._running = False
        response.success = True
        response.message = "Conveyor stopping"
        return response

    def _picked_cb(self, msg: String):
        name = msg.data.strip()
        with self._boxes_lock:
            if name in self._boxes:
                self._boxes[name]["picked"] = True
                self.get_logger().info(f"Box '{name}' marked as picked")

    def _belt_loop(self):
        self._publish_status("Conveyor running")
        next_spawn = time.time()

        while rclpy.ok() and self._running:
            now = time.time()

            # Spawn new box
            if now >= next_spawn:
                self._spawn_box()
                next_spawn = now + self._spawn_interval

            # Move all active boxes
            with self._boxes_lock:
                names = list(self._boxes.keys())

            for name in names:
                with self._boxes_lock:
                    box = self._boxes.get(name)
                if box is None or box.get("picked"):
                    continue

                box["x"] -= self._belt_speed * 0.1  # move 100 ms worth

                self._move_box(name, box["x"], self._belt_y, self._belt_z)

                # Reached pick zone?
                if box["x"] <= self._pick_x + 0.02 and not box.get("announced"):
                    box["announced"] = True
                    box["arrived_at"] = time.time()
                    self._ready_pub.publish(
                        String(data=f"{name} {box['color']}")
                    )
                    self._publish_status(
                        f"Object ready: {name} ({box['color']}) at pick zone"
                    )
                    self.get_logger().info(
                        f"Box {name} arrived at pick zone"
                    )

                # Hold timeout — despawn if not picked
                arrived = box.get("arrived_at")
                if arrived and (time.time() - arrived) > self._hold_timeout:
                    self.get_logger().warn(
                        f"Box {name} not picked in {self._hold_timeout}s — despawning"
                    )
                    self._despawn_box(name)

            time.sleep(0.1)

        self._publish_status("Conveyor stopped")

    def _spawn_box(self):
        color = random.choice(list(COLORS.keys()))
        self._counter += 1
        name = f"conv_box_{self._counter}"

        sdf = _make_box_sdf(name, ENTRY_X, self._belt_y, self._belt_z, color)

        try:
            result = subprocess.run(
                [
                    "gz", "service",
                    "-s", f"/world/{self._world}/create",
                    "--reqtype", "gz.msgs.EntityFactory",
                    "--reptype", "gz.msgs.Boolean",
                    "--timeout", "2000",
                    "--req",
                    f'sdf: "{sdf.replace(chr(10), " ").replace(chr(34), chr(39))}"'
                    f' name: "{name}"',
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                self._try_spawn_via_ros2(name, sdf, color)
            else:
                self.get_logger().info(f"Spawned {name} ({color})")
                with self._boxes_lock:
                    self._boxes[name] = {
                        "color": color, "x": ENTRY_X,
                        "picked": False, "announced": False,
                    }
        except Exception as exc:
            self.get_logger().warn(f"gz spawn failed ({exc}) — trying ros2 service")
            self._try_spawn_via_ros2(name, sdf, color)

    def _try_spawn_via_ros2(self, name: str, sdf: str, color: str):
        """Fallback: spawn via ros_gz_sim create service."""
        import tempfile, os
        with tempfile.NamedTemporaryFile(
            suffix=".sdf", mode="w", delete=False
        ) as f:
            f.write(sdf)
            sdf_path = f.name

        try:
            result = subprocess.run(
                [
                    "ros2", "run", "ros_gz_sim", "create",
                    "-world", self._world,
                    "-file", sdf_path,
                    "-name", name,
                    "-x", str(ENTRY_X),
                    "-y", str(self._belt_y),
                    "-z", str(self._belt_z),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                self.get_logger().info(f"Spawned {name} ({color}) via ros_gz_sim")
                with self._boxes_lock:
                    self._boxes[name] = {
                        "color": color, "x": ENTRY_X,
                        "picked": False, "announced": False,
                    }
            else:
                self.get_logger().error(
                    f"spawn failed: {result.stderr[:200]}"
                )
        except Exception as exc:
            self.get_logger().error(f"ros2 spawn also failed: {exc}")
        finally:
            try:
                os.unlink(sdf_path)
            except OSError:
                pass

    def _move_box(self, name: str, x: float, y: float, z: float):
        try:
            subprocess.run(
                [
                    "gz", "service",
                    "-s", f"/world/{self._world}/set_pose",
                    "--reqtype", "gz.msgs.Pose",
                    "--reptype", "gz.msgs.Boolean",
                    "--timeout", "500",
                    "--req",
                    f'name: "{name}" '
                    f'position {{ x: {x:.4f} y: {y:.4f} z: {z:.4f} }} '
                    f'orientation {{ x: 0 y: 0 z: 0 w: 1 }}',
                ],
                capture_output=True,
                timeout=2,
            )
        except Exception:
            pass  # movement failures are non-fatal; box keeps last position

    def _despawn_box(self, name: str):
        try:
            subprocess.run(
                [
                    "gz", "service",
                    "-s", f"/world/{self._world}/remove",
                    "--reqtype", "gz.msgs.Entity",
                    "--reptype", "gz.msgs.Boolean",
                    "--timeout", "2000",
                    "--req", f'name: "{name}" type: 2',
                ],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass
        with self._boxes_lock:
            self._boxes.pop(name, None)
        self.get_logger().info(f"Despawned {name}")

    def _publish_status(self, text: str):
        self._status_pub.publish(String(data=text))


def main(args=None):
    rclpy.init(args=args)
    node = ConveyorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
