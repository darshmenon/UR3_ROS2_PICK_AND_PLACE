#!/usr/bin/env python3
"""
Step-by-step motion test — tests each action individually to find what works.

Usage:
    source install/setup.bash
    python3 testing/test_steps.py [step]

Steps:
    1 - move to home (Pilz PTP joint-space)
    2 - open gripper
    3 - close gripper
    4 - IK test: compute IK for pre-grasp pose above blue block
    5 - move to pre-grasp pose above blue block (IK + Pilz PTP)
    6 - move to grasp pose (IK + Pilz PTP)
    7 - full pick sequence (home → open → pre-grasp → grasp → close → lift)
    all - run steps 1-7 in order (stop on first failure)
"""

import sys
import threading
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

# Blue block in colored_blocks.world
BLUE_X, BLUE_Y, BLUE_Z = 0.25, 0.10, 0.08
PREGRASP_Z = BLUE_Z + 0.12  # 12 cm above block


def make_downward_pose(x, y, z):
    """Create a PoseStamped with end-effector pointing down (180° rotation about X)."""
    pose = PoseStamped()
    pose.header.frame_id = "base_link"
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.position.z = z
    pose.pose.orientation.x = 1.0
    pose.pose.orientation.y = 0.0
    pose.pose.orientation.z = 0.0
    pose.pose.orientation.w = 0.0
    return pose


def spin_node(node):
    ex = SingleThreadedExecutor()
    ex.add_node(node)
    t = threading.Thread(target=ex.spin, daemon=True)
    t.start()
    return ex


def wait_servers(ex_obj, timeout=15.0):
    ex_obj.wait_for_servers(timeout=timeout)


def step1_home(ex_obj, node):
    node.get_logger().info("=== STEP 1: Move to home ===")
    ok = ex_obj.move_to_named_pose("arm", "home")
    node.get_logger().info(f"Step 1 result: {'OK' if ok else 'FAILED'}")
    return ok


def step2_open(ex_obj, node):
    node.get_logger().info("=== STEP 2: Open gripper ===")
    ok = ex_obj.open_gripper()
    node.get_logger().info(f"Step 2 result: {'OK' if ok else 'FAILED'}")
    return ok


def step3_close(ex_obj, node):
    node.get_logger().info("=== STEP 3: Close gripper ===")
    ok = ex_obj.close_gripper()
    node.get_logger().info(f"Step 3 result: {'OK' if ok else 'FAILED'}")
    return ok


def step4_ik(ex_obj, node):
    node.get_logger().info("=== STEP 4: IK test for pre-grasp pose ===")
    pose = make_downward_pose(BLUE_X, BLUE_Y, PREGRASP_Z)
    joints = ex_obj._compute_ik(pose, "arm", timeout=5.0)
    if joints:
        node.get_logger().info(f"IK solution: {[f'{v:.3f}' for v in joints]}")
        return True
    node.get_logger().error("Step 4: IK FAILED")
    return False


def step5_pregrasp(ex_obj, node):
    node.get_logger().info(f"=== STEP 5: Move to pre-grasp ({BLUE_X}, {BLUE_Y}, {PREGRASP_Z:.3f}) ===")
    pose = make_downward_pose(BLUE_X, BLUE_Y, PREGRASP_Z)
    ok = ex_obj.move_to_pose(pose)
    node.get_logger().info(f"Step 5 result: {'OK' if ok else 'FAILED'}")
    return ok


def step6_grasp(ex_obj, node):
    node.get_logger().info(f"=== STEP 6: Move to grasp ({BLUE_X}, {BLUE_Y}, {BLUE_Z + 0.01:.3f}) ===")
    pose = make_downward_pose(BLUE_X, BLUE_Y, BLUE_Z + 0.01)
    ok = ex_obj.move_to_pose(pose)
    node.get_logger().info(f"Step 6 result: {'OK' if ok else 'FAILED'}")
    return ok


def step7_full_pick(ex_obj, node):
    node.get_logger().info("=== STEP 7: Full pick sequence ===")
    tasks = [
        {"action": "move_to_named_pose", "pose_name": "home"},
        {"action": "open_gripper"},
        {"action": "pick", "object_id": "blue_block",
         "object_x": BLUE_X, "object_y": BLUE_Y, "object_z": BLUE_Z},
    ]
    ok = ex_obj.execute_task_list(tasks)
    node.get_logger().info(f"Step 7 result: {'OK' if ok else 'FAILED'}")
    return ok


STEPS = {
    "1": step1_home,
    "2": step2_open,
    "3": step3_close,
    "4": step4_ik,
    "5": step5_pregrasp,
    "6": step6_grasp,
    "7": step7_full_pick,
}


def main():
    step_arg = sys.argv[1] if len(sys.argv) > 1 else "all"

    rclpy.init()
    node = Node("test_steps")
    executor = spin_node(node)

    from ur_llm_planner.motion_executor import MotionExecutor
    ex_obj = MotionExecutor(node)
    node.get_logger().info("Waiting for action servers...")
    ex_obj.wait_for_servers(timeout=15.0)

    if step_arg == "all":
        for k in sorted(STEPS.keys()):
            if not STEPS[k](ex_obj, node):
                node.get_logger().error(f"Stopping at step {k}")
                break
    elif step_arg in STEPS:
        STEPS[step_arg](ex_obj, node)
    else:
        node.get_logger().error(f"Unknown step '{step_arg}'. Use 1-7 or 'all'")

    executor.shutdown()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
