#!/usr/bin/env python3
"""
Policy benchmark harness — OpenVLA vs MTC.

Runs N trials for each active policy on the same task (pick red object,
place at target), measures success rate and cycle time, writes results
to CSV and prints a summary table.

Usage:
    # Benchmark both policies, 5 trials each
    python3 testing/benchmark_policies.py --trials 5

    # Benchmark only MTC, 10 trials
    python3 testing/benchmark_policies.py --policies mtc --trials 10

    # Use a custom output path
    python3 testing/benchmark_policies.py --output ~/results/bench.csv

Prerequisites:
    - Gazebo + MoveIt simulation must be running:
        ros2 launch ur_gazebo ur.gazebo.launch.py
    - For OpenVLA: model is downloaded on first run (~15 GB)
    - For MTC:    ur_mtc_pick_place_demo must be running

Results CSV columns:
    policy, trial, success, cycle_time_s, pick_x, pick_y, pick_z,
    place_x, place_y, place_z, notes
"""

import argparse
import csv
import json
import math
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from std_msgs.msg import String
from std_srvs.srv import Trigger
from sensor_msgs.msg import JointState
from ur_interfaces.msg import DetectedObjectArray
from geometry_msgs.msg import Point

SENSOR_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
)

# ── task definition ──────────────────────────────────────────────────────────
# Each trial uses one of these pick targets (randomised within bounds)
PICK_X_RANGE = (0.25, 0.45)
PICK_Y_RANGE = (-0.15, 0.15)
PICK_Z       = 0.08
PLACE_TARGET = (0.50, 0.25, 0.08)

# Joint tolerance to decide if a move "succeeded" (gripper moved to target area)
SUCCESS_XY_TOL = 0.06  # metres — object must land within this radius of PLACE_TARGET

# Per-trial timeout (seconds)
TRIAL_TIMEOUT = 90.0


class BenchmarkNode(Node):
    def __init__(self):
        super().__init__("policy_benchmark")

        self._joint_states = None
        self._latest_objects = []
        self._objects_lock = __import__("threading").Lock()

        self.create_subscription(JointState, "/joint_states", self._js_cb, 10)
        self.create_subscription(
            DetectedObjectArray, "/detected_objects", self._obj_cb, SENSOR_QOS
        )

        # Publisher to send LLM planner commands (for MTC + LLM path)
        self._cmd_pub = self.create_publisher(String, "/llm_planner/command", 10)

        # Status / result tracking
        self._trial_result: dict | None = None
        self._result_lock = __import__("threading").Lock()

    def _js_cb(self, msg):
        self._joint_states = msg

    def _obj_cb(self, msg):
        with self._objects_lock:
            self._latest_objects = list(msg.objects)

    def detected_objects(self):
        with self._objects_lock:
            return list(self._latest_objects)

    # ── trial runners ─────────────────────────────────────────────────────────

    def run_mtc_trial(self, pick_x, pick_y, pick_z, place_xyz) -> dict:
        """
        MTC trial via LLM planner command string.
        The LLM planner + motion executor handle the rest.
        """
        cmd = (
            f"pick the red object at position "
            f"x={pick_x:.3f} y={pick_y:.3f} z={pick_z:.3f} "
            f"and place it at x={place_xyz[0]:.3f} y={place_xyz[1]:.3f} z={place_xyz[2]:.3f}"
        )
        return self._run_llm_cmd_trial(cmd, place_xyz)

    def run_openvla_trial(self, pick_x, pick_y, pick_z, place_xyz) -> dict:
        """OpenVLA trial: start inference node, check convergence."""
        return self._run_policy_node_trial(
            "ur_smolvla", "inference_node", place_xyz,
            extra_params={"task": "pick the red block and place it in the target zone"}
        )

    def _run_llm_cmd_trial(self, cmd: str, place_xyz: tuple) -> dict:
        start = time.time()
        msg = String()
        msg.data = cmd
        self._cmd_pub.publish(msg)

        self.get_logger().info(f"  Sent command: {cmd[:60]}…")

        # Wait for an object to appear near the place target (success) or timeout
        return self._wait_for_placement(start, place_xyz, TRIAL_TIMEOUT)

    def _run_policy_node_trial(self, pkg: str, exe: str, place_xyz: tuple, extra_params: dict) -> dict:
        """
        Launch a policy node subprocess, let it run until timeout,
        then check whether an object landed near the target.
        """
        import subprocess
        import signal

        params = " ".join(f"{k}:={v}" for k, v in extra_params.items() if v)
        cmd_str = f"ros2 run {pkg} {exe} {params}"
        self.get_logger().info(f"  Launching: {cmd_str}")

        proc = subprocess.Popen(cmd_str, shell=True, preexec_fn=os.setsid)
        start = time.time()

        result = self._wait_for_placement(start, place_xyz, TRIAL_TIMEOUT)

        # Kill the policy node after the trial
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass

        return result

    def _wait_for_placement(self, start: float, place_xyz: tuple, timeout: float) -> dict:
        """Poll detected objects until one lands near place_xyz or timeout."""
        px, py, pz = place_xyz

        while time.time() - start < timeout:
            rclpy.spin_once(self, timeout_sec=0.5)
            for obj in self.detected_objects():
                dist_xy = math.hypot(
                    obj.position.x - px,
                    obj.position.y - py,
                )
                if dist_xy < SUCCESS_XY_TOL:
                    elapsed = time.time() - start
                    return {"success": True, "cycle_time_s": round(elapsed, 2)}

        elapsed = time.time() - start
        return {"success": False, "cycle_time_s": round(elapsed, 2)}


# ── main ─────────────────────────────────────────────────────────────────────

POLICY_RUNNERS = {
    "mtc":    "run_mtc_trial",
    "openvla": "run_openvla_trial",
}


def parse_args():
    p = argparse.ArgumentParser(description="Benchmark UR3 pick-place policies")
    p.add_argument("--policies", nargs="+", default=["mtc", "openvla"],
                   choices=list(POLICY_RUNNERS.keys()),
                   help="Which policies to benchmark")
    p.add_argument("--trials", type=int, default=5,
                   help="Number of trials per policy")
    p.add_argument("--output", default="",
                   help="CSV output path (default: logs/benchmark_<timestamp>.csv)")
    p.add_argument("--seed", type=int, default=42,
                   help="Random seed for pick position sampling")
    return p.parse_args()


def main():
    args = parse_args()
    rng = random.Random(args.seed)

    rclpy.init()
    node = BenchmarkNode()

    out_path = args.output or (
        Path(__file__).parent.parent / "logs" /
        f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    place_xyz = PLACE_TARGET
    all_results = []

    header = [
        "policy", "trial", "success", "cycle_time_s",
        "pick_x", "pick_y", "pick_z", "place_x", "place_y", "place_z",
    ]

    print(f"\nBenchmarking policies: {args.policies}  ×  {args.trials} trials each")
    print(f"Output: {out_path}\n")

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        for policy in args.policies:
            runner = getattr(node, POLICY_RUNNERS[policy])
            successes = []
            times = []

            print(f"── {policy.upper()} ──────────────────────────────────────")
            for trial in range(1, args.trials + 1):
                pick_x = rng.uniform(*PICK_X_RANGE)
                pick_y = rng.uniform(*PICK_Y_RANGE)

                print(f"  Trial {trial}/{args.trials}  pick=({pick_x:.3f},{pick_y:.3f},{PICK_Z:.3f})", end="  ", flush=True)

                result = runner(pick_x, pick_y, PICK_Z, place_xyz)

                status = "✓" if result["success"] else "✗"
                print(f"{status}  {result['cycle_time_s']:.1f}s")

                row = {
                    "policy": policy,
                    "trial": trial,
                    "success": result["success"],
                    "cycle_time_s": result["cycle_time_s"],
                    "pick_x": round(pick_x, 4),
                    "pick_y": round(pick_y, 4),
                    "pick_z": PICK_Z,
                    "place_x": place_xyz[0],
                    "place_y": place_xyz[1],
                    "place_z": place_xyz[2],
                }
                writer.writerow(row)
                f.flush()
                all_results.append(row)
                successes.append(result["success"])
                times.append(result["cycle_time_s"])

            rate = sum(successes) / len(successes) * 100
            avg_t = sum(times) / len(times)
            print(f"  → {policy}: {rate:.0f}% success  avg {avg_t:.1f}s/trial\n")

    # Summary table
    print("═" * 50)
    print(f"{'Policy':<12} {'Success':>8} {'Avg time':>10} {'Min':>8} {'Max':>8}")
    print("─" * 50)
    for policy in args.policies:
        rows = [r for r in all_results if r["policy"] == policy]
        n = len(rows)
        if not n:
            continue
        s_rate = sum(r["success"] for r in rows) / n * 100
        times_p = [r["cycle_time_s"] for r in rows]
        print(f"{policy:<12} {s_rate:>7.0f}%  {sum(times_p)/n:>9.1f}s  {min(times_p):>6.1f}s  {max(times_p):>6.1f}s")
    print("═" * 50)
    print(f"\nFull results: {out_path}")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
