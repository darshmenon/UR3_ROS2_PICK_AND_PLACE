#!/usr/bin/env python3
"""
Planner benchmark harness — Pilz PTP/LIN vs OMPL RRTConnect.

testing/test_planners.py already smoke-tests every planner/executor
combination once (pass/fail only). This runs each case N times and records
wall-clock planning time + success rate, since OMPL in particular is
stochastic and a single run tells you nothing about consistency.

OMPL cases use plan_only=True: this project's Humble MoveIt build has no
response_adapter time-parameterization plugins, so OMPL trajectories always
hit CONTROL_FAILED on execution (see test_planners.py's test_ompl_* — Pilz is
used for all real motion). Benchmarking plan_only here measures the actual
planner, not that known/expected execution failure.

Usage:
    source install/setup.bash
    python3 testing/benchmark_planners.py --trials 10

Prerequisites:
    - Gazebo + MoveIt simulation must be running:
        ros2 launch ur_gazebo ur.gazebo.launch.py

Results CSV columns:
    case, trial, success, error_code, planning_time_s
"""

import argparse
import csv
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import rclpy
from geometry_msgs.msg import PoseStamped
from moveit_msgs.action import MoveGroup as MoveGroupAction
from moveit_msgs.msg import MoveItErrorCodes
from rclpy.action import ActionClient
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node

sys.path.insert(0, str(Path(__file__).parent))
from test_planners import (  # noqa: E402
    BLUE_X, BLUE_Y, BLUE_Z, GREEN_X, GREEN_Y, GREEN_Z, HOME_JOINTS,
    _ARM_JOINTS, _build_cartesian_req, _build_joint_req, _error_name,
    downward_pose,
)

CASES = [
    "pilz_ptp_home", "pilz_ptp_blue", "pilz_ptp_green", "pilz_lin",
    "ompl_home", "ompl_ik_blue",
]


def timed_send(node, move_client, req, plan_only, timeout=30.0):
    """Send a MoveGroup goal, return (success, error_name, elapsed_s)."""
    goal = MoveGroupAction.Goal()
    goal.request = req
    goal.planning_options.plan_only = plan_only
    goal.planning_options.replan = False

    start = time.time()
    future = move_client.send_goal_async(goal)
    deadline = start + timeout
    while not future.done():
        if time.time() > deadline:
            return False, "send_goal timeout", time.time() - start
        time.sleep(0.02)

    handle = future.result()
    if not handle.accepted:
        return False, "goal rejected", time.time() - start

    result_future = handle.get_result_async()
    while not result_future.done():
        if time.time() > deadline:
            return False, "result timeout", time.time() - start
        time.sleep(0.02)

    elapsed = time.time() - start
    code = result_future.result().result.error_code.val
    return code == MoveItErrorCodes.SUCCESS, _error_name(code), elapsed


def run_case(case, node, move_client, ex_obj):
    if case == "pilz_ptp_home":
        start = time.time()
        ok = ex_obj.move_to_named_pose("arm", "home")
        return ok, "SUCCESS" if ok else "FAILED", time.time() - start

    if case == "pilz_ptp_blue":
        start = time.time()
        ok = ex_obj.move_to_pose(downward_pose(BLUE_X, BLUE_Y, BLUE_Z))
        return ok, "SUCCESS" if ok else "FAILED", time.time() - start

    if case == "pilz_ptp_green":
        start = time.time()
        ok = ex_obj.move_to_pose(downward_pose(GREEN_X, GREEN_Y, GREEN_Z))
        return ok, "SUCCESS" if ok else "FAILED", time.time() - start

    if case == "pilz_lin":
        ex_obj.move_to_pose(downward_pose(BLUE_X, BLUE_Y, BLUE_Z))  # short valid start
        req = _build_cartesian_req(
            node, pipeline_id="pilz_industrial_motion_planner", planner_id="LIN",
            x=BLUE_X, y=BLUE_Y, z=BLUE_Z - 0.05,
        )
        return timed_send(node, move_client, req, plan_only=False)

    if case == "ompl_home":
        req = _build_joint_req(
            node, pipeline_id="ompl", planner_id="RRTConnectkConfigDefault",
            joints=HOME_JOINTS,
        )
        return timed_send(node, move_client, req, plan_only=True)

    if case == "ompl_ik_blue":
        joints = ex_obj._compute_ik(downward_pose(BLUE_X, BLUE_Y, BLUE_Z), "arm", timeout=5.0)
        if joints is None:
            return False, "NO_IK_SOLUTION", 0.0
        req = _build_joint_req(
            node, pipeline_id="ompl", planner_id="RRTConnectkConfigDefault",
            joints=dict(zip(_ARM_JOINTS, joints)),
        )
        return timed_send(node, move_client, req, plan_only=True)

    raise ValueError(case)


def main():
    ap = argparse.ArgumentParser(description="Benchmark UR3 planner combinations")
    ap.add_argument("--cases", nargs="+", default=CASES, choices=CASES)
    ap.add_argument("--trials", type=int, default=10, help="Repeats per case")
    ap.add_argument("--output", default="", help="CSV output path")
    args = ap.parse_args()

    rclpy.init()
    node = Node("benchmark_planners")
    executor = SingleThreadedExecutor()
    executor.add_node(node)
    threading.Thread(target=executor.spin, daemon=True).start()

    from ur_llm_planner.motion_executor import MotionExecutor
    ex_obj = MotionExecutor(node)

    node.get_logger().info("Waiting for servers (15 s)...")
    if not ex_obj.wait_for_servers(timeout=15.0):
        print("ERROR: servers not ready")
        sys.exit(1)

    move_client = ActionClient(node, MoveGroupAction, "/move_action")
    move_client.wait_for_server(timeout_sec=15.0)

    out_path = args.output or (
        Path(__file__).parent.parent / "logs" /
        f"planner_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    print(f"\nBenchmarking cases: {args.cases}  ×  {args.trials} trials each")
    print(f"Output: {out_path}\n")

    header = ["case", "trial", "success", "error_code", "planning_time_s"]
    all_rows = []
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()

        for case in args.cases:
            print(f"── {case} ──────────────────────────────────────")
            for trial in range(1, args.trials + 1):
                if case == "pilz_ptp_home":
                    # Reset to a pose AWAY from home: the case itself moves to
                    # "home", and Pilz PTP returns INVALID_MOTION_PLAN for a
                    # zero-distance goal (start == goal), which would count as a
                    # false failure here if we reset to home first.
                    # MotionExecutor.move_to_named_pose only knows "home"/"ready"
                    # (and they're numerically identical -- see ur.srdf), and an
                    # IK-derived move_to_pose() reset can land on an out-of-range
                    # unwrapped solution (e.g. wrist_1 > pi) that then makes the
                    # *next* Pilz PTP plan back to home fail for real. Go through
                    # raw MoveGroup with a small joint-space offset instead.
                    reset_joints = dict(HOME_JOINTS)
                    reset_joints["shoulder_pan_joint"] += 0.3
                    reset_req = _build_joint_req(
                        node, pipeline_id="pilz_industrial_motion_planner",
                        planner_id="PTP", joints=reset_joints,
                    )
                    timed_send(node, move_client, reset_req, plan_only=False)
                else:
                    ex_obj.move_to_named_pose("arm", "home")  # reset between trials
                success, err, elapsed = run_case(case, node, move_client, ex_obj)
                status = "✓" if success else "✗"
                print(f"  Trial {trial}/{args.trials}  {status}  {elapsed:.2f}s  ({err})")
                row = {"case": case, "trial": trial, "success": success,
                       "error_code": err, "planning_time_s": round(elapsed, 4)}
                writer.writerow(row)
                f.flush()
                all_rows.append(row)

    print("\n" + "=" * 60)
    print(f"{'Case':<16} {'Success':>8} {'Avg time':>10} {'Min':>8} {'Max':>8}")
    print("-" * 60)
    for case in args.cases:
        rows = [r for r in all_rows if r["case"] == case]
        n = len(rows)
        if not n:
            continue
        rate = sum(r["success"] for r in rows) / n * 100
        times = [r["planning_time_s"] for r in rows]
        print(f"{case:<16} {rate:>7.0f}%  {sum(times)/n:>9.2f}s  {min(times):>6.2f}s  {max(times):>6.2f}s")
    print("=" * 60)
    print(f"\nFull results: {out_path}")

    ex_obj.move_to_named_pose("arm", "home")
    executor.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
