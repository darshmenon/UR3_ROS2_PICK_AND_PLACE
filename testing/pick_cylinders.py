#!/usr/bin/env python3
"""
pick_cylinders.py — sequential hierarchical pick-and-place for cylinders.

Hierarchy
─────────
  Task 1: PICK BLUE  → place in bin_left
  Task 2: PICK GREEN → place in bin_right
  Task 3: PICK RED   → place in bin_left  (pick_and_place_demo.world)

Each task is broken into phases:
  INIT      → home + open gripper
  PRE_GRASP → hover above cylinder
  DESCEND   → lower to grasp height
  GRASP     → close gripper
  LIFT      → raise to carry height
  TRANSPORT → move above bin
  LOWER     → descend into bin
  RELEASE   → open gripper
  RETREAT   → lift away from bin
  RETURN    → back to home

Grasp algorithm (centroid-based IK)
────────────────────────────────────
  1. Known cylinder centre (x,y) from world file
  2. Grasp z = ~30% of cylinder height (good friction contact point)
  3. Pre-grasp z = grasp_z + PREGRASP_HEIGHT_OFFSET (hover approach)
  4. IK solved via KDL from natural downward-grasp seed
  5. Pilz PTP executes collision-free joint trajectory

Usage
─────
  source install/setup.bash
  python3 testing/pick_cylinders.py           # blue + green (colored_blocks.world)
  python3 testing/pick_cylinders.py --red     # red cylinder (pick_and_place_demo.world)
  python3 testing/pick_cylinders.py --blue    # only blue block
  python3 testing/pick_cylinders.py --green   # only green block
  python3 testing/pick_cylinders.py --all     # all three
  python3 testing/pick_cylinders.py --dry     # print plan, don't execute
"""

import argparse
import sys
import threading
import time

import rclpy
from rclpy.node import Node

# World positions  (from colored_blocks.world)
# Cylinders: radius=0.025 m, height=0.15 m, centre_z=0.075 m
# Grasp z: tool reaches ~2/3 up the cylinder
BLUE_BLOCK   = dict(x=0.25,  y=0.10,  z=0.06)   # grasp at lower-1/3 of 15cm cylinder
GREEN_BLOCK  = dict(x=0.30,  y=-0.05, z=0.06)
RED_CYLINDER = dict(x=0.22,  y=0.12,  z=0.12)   # 40cm cylinder, grasp at 30% height

# Bins: flat trays at z≈0.005 m; place the cylinder so its bottom clears the tray
BIN_LEFT  = dict(x=-0.15, y=0.25,  z=0.06)   # tool height when releasing
BIN_RIGHT = dict(x=-0.15, y=-0.25, z=0.06)

# Carry height between pick and place (m) — used for TRANSPORT phase
CARRY_Z = 0.22

# ── Task plan ────────────────────────────────────────────────────────────────

def build_plan(blue: bool = True, green: bool = True, red: bool = False) -> list[dict]:
    """Return the flat ordered task list for the requested cylinders."""
    tasks: list[dict] = []

    def init():
        tasks.append({"action": "move_to_named_pose", "pose_name": "home",
                       "phase": "INIT", "desc": "Return to home", "optional": True})
        tasks.append({"action": "open_gripper",
                       "phase": "INIT", "desc": "Open gripper"})

    def pick_cylinder(name: str, pos: dict, bin_pos: dict):
        cx, cy, cz = pos["x"], pos["y"], pos["z"]
        bx, by, bz = bin_pos["x"], bin_pos["y"], bin_pos["z"]
        tasks.append({
            "action": "pick",
            "object_id": name,
            "object_x": cx, "object_y": cy, "object_z": cz,
            "phase": f"PICK_{name.upper()}",
            "desc": f"Pick {name} at ({cx:.2f}, {cy:.2f}, {cz:.2f})",
        })
        # Explicit TRANSPORT via a carry-height intermediate before place
        tasks.append({
            "action": "_move_xyz",
            "x": bx, "y": by, "z": CARRY_Z,
            "phase": "TRANSPORT",
            "desc": f"Carry {name} above bin ({bx:.2f},{by:.2f}) at z={CARRY_Z:.2f}",
        })
        tasks.append({
            "action": "place",
            "x": bx, "y": by, "z": bz,
            "phase": f"PLACE_{name.upper()}",
            "desc": f"Place {name} in bin at ({bx:.2f}, {by:.2f}, {bz:.2f})",
        })

    init()
    if blue:
        pick_cylinder("blue_block", BLUE_BLOCK, BIN_LEFT)
        tasks.append({"action": "move_to_named_pose", "pose_name": "home",
                       "phase": "RETURN", "desc": "Return to home between tasks",
                       "optional": True})
    if green:
        pick_cylinder("green_block", GREEN_BLOCK, BIN_RIGHT)
        tasks.append({"action": "move_to_named_pose", "pose_name": "home",
                       "phase": "RETURN", "desc": "Return to home between tasks",
                       "optional": True})
    if red:
        pick_cylinder("red_cylinder", RED_CYLINDER, BIN_LEFT)
    tasks.append({"action": "move_to_named_pose", "pose_name": "home",
                   "phase": "DONE", "desc": "Final home", "optional": True})
    return tasks


# ── Runner node ───────────────────────────────────────────────────────────────

class CylinderPickNode(Node):
    def __init__(self, tasks: list[dict]):
        super().__init__("cylinder_pick")
        # Import here so this script is usable even if the package isn't installed
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from ur_llm_planner.motion_executor import MotionExecutor

        self._tasks = tasks
        self._executor_obj = MotionExecutor(self)
        self._done = threading.Event()
        self._result: bool = False
        # Start execution in a thread so rclpy.spin() keeps running
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.get_logger().info("Waiting for action servers (20 s)...")
        if not self._executor_obj.wait_for_servers(timeout=20.0):
            self.get_logger().error("Servers not ready — aborting.")
            self._done.set()
            return

        self.get_logger().info(
            f"Starting sequential pick plan ({len(self._tasks)} steps)"
        )
        _print_plan(self._tasks)

        success = True
        for i, task in enumerate(self._tasks):
            phase = task.get("phase", "?")
            desc  = task.get("desc",  task.get("action", "?"))
            action = task.get("action", "")

            print(f"\n{'─'*60}")
            print(f"  [{i+1:02d}/{len(self._tasks):02d}]  {phase}  |  {desc}")
            print(f"{'─'*60}")

            if action == "_move_xyz":
                # Intermediate carry-height move not in MotionExecutor.execute_task_list
                from geometry_msgs.msg import PoseStamped
                pose = PoseStamped()
                pose.header.frame_id = "base_link"
                pose.pose.position.x = task["x"]
                pose.pose.position.y = task["y"]
                pose.pose.position.z = task["z"]
                pose.pose.orientation.x = 1.0  # downward orientation
                pose.pose.orientation.w = 0.0
                ok = self._executor_obj.move_to_pose(pose)
            else:
                ok = self._executor_obj._dispatch_task(task)

            status = "✅ OK" if ok else "❌ FAILED"
            print(f"  → {status}")

            if not ok:
                if task.get("optional", False):
                    print(f"  → ⚠️  optional step failed — continuing")
                else:
                    self.get_logger().error(f"Step {i+1} failed ({phase}) — aborting.")
                    success = False
                    break

        if success:
            print(f"\n{'═'*60}")
            print("  ALL TASKS COMPLETE")
            print(f"{'═'*60}\n")
        else:
            print(f"\n{'═'*60}")
            print("  SEQUENCE ABORTED — see errors above")
            print(f"{'═'*60}\n")

        self._result = success
        self._done.set()


# ── Helpers ──────────────────────────────────────────────────────────────────

def _print_plan(tasks: list[dict]) -> None:
    print(f"\n{'═'*60}")
    print("  SEQUENTIAL PICK PLAN")
    print(f"{'═'*60}")
    current_phase = None
    for i, t in enumerate(tasks):
        phase = t.get("phase", "?")
        if phase != current_phase:
            print(f"\n  ── {phase}")
            current_phase = phase
        print(f"     [{i+1:02d}] {t.get('desc', t.get('action', '?'))}")
    print(f"\n{'═'*60}\n")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blue",  action="store_true", help="Pick blue block")
    ap.add_argument("--green", action="store_true", help="Pick green block")
    ap.add_argument("--red",   action="store_true", help="Pick red cylinder (pick_and_place_demo.world)")
    ap.add_argument("--all",   action="store_true", help="Pick all three")
    ap.add_argument("--dry",   action="store_true", help="Print plan without executing")
    args = ap.parse_args()

    any_flag = args.blue or args.green or args.red or args.all
    blue  = args.all or args.blue  or not any_flag   # default: blue+green
    green = args.all or args.green or not any_flag
    red   = args.all or args.red

    tasks = build_plan(blue=blue, green=green, red=red)

    if args.dry:
        _print_plan(tasks)
        return

    rclpy.init()
    node = CylinderPickNode(tasks)

    # spin in daemon thread so action callbacks fire reliably
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    node._done.wait()
    success = node._result
    rclpy.shutdown()
    spin_thread.join(timeout=2.0)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
