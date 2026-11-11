#!/usr/bin/env python3
"""Peg-in-hole task for the Cartesian impedance controller (Gazebo).

Drives ~/target_pose of cartesian_impedance_controller: hover over the hole, descend at --speed, and (with
search:=true) spiral the commanded xy outward under a light press when the peg lands on the top face.
Contact force is the impedance spring force K (x_des - x), i.e. what the controller is commanding against the contact;
it is logged to a CSV together with tip pose, depth and task mode. Positions are in the URDF root frame, which includes the table height (hole top face z = 1.135).

  ros2 run ur_force_control peg_in_hole_task --ros-args -p use_sim_time:=true -p offset_x:=0.0015 -p search:=true
"""
import csv
import math

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from std_srvs.srv import Trigger

HOLE_DEPTH = 0.03


class PegInHoleTask(Node):
    def __init__(self):
        super().__init__("peg_in_hole_task")
        p = self.declare_parameter
        self.hole = [p("hole_x", 0.28).value, p("hole_y", 0.14).value, p("hole_z", 1.135).value]   # world/root frame (table top 1.015 + 0.12)
        self.off = [p("offset_x", 0.0004).value, p("offset_y", 0.0).value]
        self.hover = p("hover", 0.03).value
        self.speed = p("speed", 0.01).value
        self.k = p("stiffness", 800.0).value
        self.k_rot = p("stiffness_rot", 30.0).value
        self.search = p("search", False).value
        self.f_press = p("f_press", 3.0).value
        self.pitch = p("pitch", 0.0008).value
        self.spiral_hz = p("spiral_hz", 0.7).value
        self.k_search = p("search_stiffness_xy", 2500.0).value   # stiff xy while searching so the spring can slide the peg on the rim
        self.r_max = p("r_max", 0.006).value
        self.contact_n = p("contact_threshold", 2.0).value
        self.t_end = p("t_end", 25.0).value
        self.settle = p("settle", 3.0).value
        self.csv_path = p("log_csv", "/tmp/peg_in_hole_gazebo.csv").value

        self.goal = [self.hole[0] + self.off[0], self.hole[1] + self.off[1]]
        self.z0 = self.hole[2] + self.hover
        self.z_floor = self.hole[2] - HOLE_DEPTH + 0.002
        self.tip = None
        self.qx = 1.0
        self.kxy = self.k
        self.mode = 0            # 0 descend, 1 search, 2 insert
        self.t0 = None
        self.t_s = self.z_c = self.t_i = self.z_i = 0.0
        self.xy_hold = list(self.goal)
        self.rows = []
        self.done = False

        self.pub = self.create_publisher(PoseStamped, "/cartesian_impedance_controller/target_pose", 10)
        self.k_pub = self.create_publisher(Float64MultiArray, "/cartesian_impedance_controller/stiffness", 10)
        self.create_subscription(PoseStamped, "/cartesian_impedance_controller/tip_pose", self.on_tip, 10)
        self.hold = self.create_client(Trigger, "/cartesian_impedance_controller/hold_current_pose")
        self.create_timer(0.01, self.tick)

    def on_tip(self, m):
        self.tip = [m.pose.position.x, m.pose.position.y, m.pose.position.z]
        self.qx = m.pose.orientation.x          # target quaternion is (x=1): angle error = 2 acos(|qx|)

    def send(self, x, y, z):
        m = PoseStamped()
        m.header.frame_id = "base_link"
        m.header.stamp = self.get_clock().now().to_msg()
        m.pose.position.x, m.pose.position.y, m.pose.position.z = x, y, z
        m.pose.orientation.x = 1.0          # tool z pointing down: 180 deg about x
        m.pose.orientation.w = 0.0          # (the message default is w=1, which would be a 90 deg rotation)
        self.pub.publish(m)

    def tick(self):
        if self.done or self.tip is None:
            return
        now = self.get_clock().now().nanoseconds * 1e-9
        if self.t0 is None:
            self.t0 = now
            self.k_pub.publish(Float64MultiArray(data=[self.k] * 3 + [self.k_rot] * 3))
        t = now - self.t0
        depth = self.hole[2] - self.tip[2]
        xy = list(self.goal)
        z = self.z0
        # phase A: move above the hole in hover pose (controller ramps via stiffness; wait for settling)
        if t < self.settle:
            self.send(self.goal[0], self.goal[1], self.z0)
            self.log(t, xy, z, depth)
            return
        ts = t - self.settle
        z = max(self.z_floor, self.z0 - self.speed * ts)
        if self.search:
            f_ax = self.k * (z - self.tip[2]) * -1.0   # spring force pushing the tip down onto the surface
            if self.mode == 0 and f_ax > self.contact_n and depth < 0.002:
                self.mode, self.t_s, self.z_c = 1, ts, self.tip[2]
                self.kxy = self.k_search
                self.k_pub.publish(Float64MultiArray(data=[self.k_search, self.k_search, self.k] + [self.k_rot] * 3))
            if self.mode == 1:
                th = 2 * math.pi * self.spiral_hz * (ts - self.t_s)
                r = min(self.r_max, self.pitch * th / (2 * math.pi))
                xy = [self.goal[0] + r * math.cos(th), self.goal[1] + r * math.sin(th)]
                z = self.z_c - self.f_press / self.k
                if depth > 0.004:
                    self.mode, self.xy_hold, self.z_i, self.t_i = 2, self.tip[:2], self.tip[2], ts
                    self.kxy = self.k
                    self.k_pub.publish(Float64MultiArray(data=[self.k] * 3 + [self.k_rot] * 3))
            if self.mode == 2:
                xy = list(self.xy_hold)
                z = max(self.z_floor, self.z_i - self.speed * (ts - self.t_i))
        self.send(xy[0], xy[1], z)
        self.log(t, xy, z, depth)
        if t > self.t_end or (depth > 0.9 * HOLE_DEPTH and t > self.settle + 2.0):
            self.finish(depth)

    def log(self, t, xy, z, depth):
        fx = self.kxy * (xy[0] - self.tip[0])
        fy = self.kxy * (xy[1] - self.tip[1])
        fz = self.k * (z - self.tip[2])
        self.rows.append([f"{t:.3f}", *[f"{v:.5f}" for v in self.tip], f"{xy[0]:.5f}", f"{xy[1]:.5f}", f"{z:.5f}",
                          f"{depth:.5f}", f"{math.hypot(fx, fy):.3f}", f"{abs(fz):.3f}", self.mode,
                          f"{math.degrees(2 * math.acos(min(1.0, abs(self.qx)))):.2f}"])

    def finish(self, depth):
        self.done = True
        with open(self.csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t", "x", "y", "z", "xd", "yd", "zd", "depth", "f_lateral", "f_axial", "mode", "rot_err_deg"])
            w.writerows(self.rows)
        ok = depth > 0.9 * HOLE_DEPTH
        self.get_logger().info(f"{'INSERTED' if ok else 'NOT inserted'}: depth={depth*1e3:.1f} mm, log -> {self.csv_path}")


def main():
    rclpy.init()
    node = PegInHoleTask()
    while rclpy.ok() and not node.done:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
