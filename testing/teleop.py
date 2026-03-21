#!/usr/bin/env python3
"""
Keyboard teleoperation for the UR3 arm.

Move individual joints or the end-effector with keyboard keys.
Sends Pilz PTP goals via the MoveGroup action server.

Usage:
    source install/setup.bash
    python3 testing/teleop.py

Controls:
    Joint mode (default):
        1-6       — select joint (1=shoulder_pan ... 6=wrist_3)
        +/=       — increment selected joint by step
        -         — decrement selected joint by step
        [/]       — decrease / increase step size
        h         — go to home pose
        r         — go to ready pose

    Cartesian mode (press c to toggle):
        w/s       — +/- X (forward/back)
        a/d       — +/- Y (left/right)
        z/x       — +/- Z (up/down)
        [/]       — decrease / increase step size

    Gripper:
        o         — open gripper
        p         — close gripper (pick)
        m         — half close

    General:
        c         — toggle joint / Cartesian mode
        q / ESC   — quit
"""

import math
import sys
import termios
import threading
import tty

import rclpy
from control_msgs.action import GripperCommand
from geometry_msgs.msg import PoseStamped
from rclpy.action import ActionClient
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState

# ── constants ─────────────────────────────────────────────────────────────────

ARM_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
HOME_JOINTS  = [0.0, -1.6663, 0.0, 0.0, 0.0, 0.0]
READY_JOINTS = [0.0, -1.6663, 0.0, 0.0, 0.0, 1.0]
JOINT_LIMITS = [
    (-6.28, 6.28), (-6.28, 6.28), (-3.14, 3.14),
    (-6.28, 6.28), (-6.28, 6.28), (-6.28, 6.28),
]
STEPS = [0.02, 0.05, 0.10, 0.20]   # available step sizes (rad or m)
CART_STEP = 0.02                   # default Cartesian step (m)

BANNER = """
╔══════════════════════════════════════════════════╗
║          UR3 Keyboard Teleoperation              ║
╠══════════════════════════════════════════════════╣
║  JOINT MODE   (press c for Cartesian mode)       ║
║  1-6  select joint   +/-  move   [/]  step size  ║
║  h  home   r  ready                              ║
║                                                  ║
║  GRIPPER:  o=open  p=close  m=half               ║
║  q / ESC = quit                                  ║
╚══════════════════════════════════════════════════╝
"""


# ── raw keyboard helper ───────────────────────────────────────────────────────

def getch():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


# ── main node ────────────────────────────────────────────────────────────────

class TeleopNode(Node):
    def __init__(self):
        super().__init__("teleop")
        self._js_sub = self.create_subscription(
            JointState, "/joint_states", self._js_cb, 10
        )
        self._current_joints = list(HOME_JOINTS)
        self._js_ready = False

    def _js_cb(self, msg: JointState):
        pos = {}
        for name, p in zip(msg.name, msg.position):
            pos[name] = p
        vals = []
        for jname in ARM_JOINTS:
            vals.append(pos.get(jname, 0.0))
        self._current_joints = vals
        self._js_ready = True


def run_teleop(node: TeleopNode):
    from ur_llm_planner.motion_executor import MotionExecutor
    ex_obj = MotionExecutor(node)

    print("Waiting for action servers...")
    if not ex_obj.wait_for_servers(timeout=15.0):
        print("ERROR: servers not ready — is the simulation running?")
        return

    print(BANNER)

    mode = "joint"          # "joint" or "cartesian"
    sel_joint = 0           # 0-indexed joint selection
    step_idx = 1            # index into STEPS list
    cart_step = CART_STEP
    busy = threading.Event()

    def status():
        step = STEPS[step_idx]
        jname = ARM_JOINTS[sel_joint]
        jval  = node._current_joints[sel_joint]
        if mode == "joint":
            print(f"\r  [JOINT] joint {sel_joint+1}: {jname:25s}  = {jval:+.3f} rad   step={step:.2f}   ", end="", flush=True)
        else:
            print(f"\r  [CART] step={cart_step:.3f} m   q=quit c=back   ", end="", flush=True)

    def move_joint(joint_idx, delta):
        if busy.is_set():
            return
        vals = list(node._current_joints)
        new_val = vals[joint_idx] + delta
        lo, hi = JOINT_LIMITS[joint_idx]
        new_val = max(lo, min(hi, new_val))
        vals[joint_idx] = new_val
        busy.set()
        def do_move():
            ex_obj._move_to_joint_values("arm", vals, timeout=5.0)
            busy.clear()
        threading.Thread(target=do_move, daemon=True).start()

    def move_named(name):
        if busy.is_set():
            return
        busy.set()
        def do_move():
            ex_obj.move_to_named_pose("arm", name)
            busy.clear()
        threading.Thread(target=do_move, daemon=True).start()

    def move_cart(dx=0.0, dy=0.0, dz=0.0):
        if busy.is_set():
            return
        # Get current end-effector pose via TF2, apply delta, move via IK+PTP
        busy.set()
        def do_move():
            try:
                import tf2_ros
                from geometry_msgs.msg import TransformStamped
                tf_buf = tf2_ros.Buffer()
                tf_lis = tf2_ros.TransformListener(tf_buf, node)
                import time; time.sleep(0.3)
                t: TransformStamped = tf_buf.lookup_transform(
                    "base_link", "tool0", rclpy.time.Time()
                )
                pose = PoseStamped()
                pose.header.frame_id = "base_link"
                pose.pose.position.x = t.transform.translation.x + dx
                pose.pose.position.y = t.transform.translation.y + dy
                pose.pose.position.z = t.transform.translation.z + dz
                pose.pose.orientation = t.transform.rotation
                ex_obj.move_to_pose(pose)
            except Exception as e:
                node.get_logger().error(f"Cartesian move failed: {e}")
            finally:
                busy.clear()
        threading.Thread(target=do_move, daemon=True).start()

    status()
    while True:
        ch = getch()

        if ch in ('\x1b', 'q'):
            print("\nQuitting.")
            break

        elif ch == 'c':
            mode = "cartesian" if mode == "joint" else "joint"
            print(f"\n  Switched to {mode.upper()} mode")

        elif ch in "123456" and mode == "joint":
            sel_joint = int(ch) - 1
            print(f"\n  Selected joint {ch}: {ARM_JOINTS[sel_joint]}")

        elif ch in ('+', '=') and mode == "joint":
            move_joint(sel_joint, STEPS[step_idx])

        elif ch == '-' and mode == "joint":
            move_joint(sel_joint, -STEPS[step_idx])

        elif ch == '[':
            step_idx = max(0, step_idx - 1)
            cart_step = STEPS[step_idx]

        elif ch == ']':
            step_idx = min(len(STEPS) - 1, step_idx + 1)
            cart_step = STEPS[step_idx]

        elif ch == 'h':
            print("\n  Going home...")
            move_named("home")

        elif ch == 'r':
            print("\n  Going to ready...")
            move_named("ready")

        elif mode == "cartesian":
            if   ch == 'w': move_cart(dx=+cart_step)
            elif ch == 's': move_cart(dx=-cart_step)
            elif ch == 'a': move_cart(dy=+cart_step)
            elif ch == 'd': move_cart(dy=-cart_step)
            elif ch == 'z': move_cart(dz=+cart_step)
            elif ch == 'x': move_cart(dz=-cart_step)

        # Gripper keys (work in both modes)
        if ch == 'o':
            print("\n  Opening gripper...")
            threading.Thread(target=ex_obj.open_gripper, daemon=True).start()
        elif ch == 'p':
            print("\n  Closing gripper...")
            threading.Thread(target=ex_obj.close_gripper, daemon=True).start()
        elif ch == 'm':
            print("\n  Half-close gripper...")
            threading.Thread(target=ex_obj.half_close_gripper, daemon=True).start()

        status()


def main():
    rclpy.init()
    node = TeleopNode()
    ex = SingleThreadedExecutor()
    ex.add_node(node)
    spin_thread = threading.Thread(target=ex.spin, daemon=True)
    spin_thread.start()

    # Wait for first joint state
    import time
    print("Waiting for joint states...")
    for _ in range(50):
        if node._js_ready:
            break
        time.sleep(0.1)

    try:
        run_teleop(node)
    finally:
        ex.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
