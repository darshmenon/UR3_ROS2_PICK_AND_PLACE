"""Offline tests for MotionExecutor internals (needs rclpy, not a simulator or move_group).

A real Node is created but never spun: the action clients and the IK client simply find no server. That is enough to test the
gripper profiles, the lost-object check and the pick pose maths, which are the parts that were wrong before.
"""
import math

import pytest

rclpy = pytest.importorskip("rclpy")
from sensor_msgs.msg import JointState  # noqa: E402

from ur_llm_planner.motion_executor import GRIPPER_PROFILES, MotionExecutor  # noqa: E402


@pytest.fixture(scope="module")
def node():
    rclpy.init()
    n = rclpy.create_node("motion_executor_test")
    yield n
    n.destroy_node()
    rclpy.shutdown()


def make(node, gripper):
    ex = MotionExecutor(node)
    ex.set_gripper(gripper)
    return ex


def joint_state(name, position):
    msg = JointState()
    msg.name = [name]
    msg.position = [position]
    return msg


@pytest.mark.parametrize("gripper", sorted(GRIPPER_PROFILES))
def test_profile_is_applied(node, gripper):
    ex = make(node, gripper)
    prof = GRIPPER_PROFILES[gripper]
    assert ex._gripper_joint_name == prof["joint"]
    assert ex._gripper_closed == prof["closed"]
    assert ex._gripper_open == prof.get("open", 0.0)
    assert ex._tcp_offset_z == prof["tcp_z"]
    assert ex._named_gripper_poses["open"] == prof.get("open", 0.0)
    assert ex._named_gripper_poses["closed"] == prof["closed"]
    expected_half = prof["closed"] * 0.75 if prof.get("open", 0.0) == 0.0 else prof["half"]
    assert ex._named_gripper_poses["half_closed"] == pytest.approx(expected_half)


def test_unknown_gripper_falls_back_to_2f85(node):
    ex = make(node, "no_such_gripper")
    assert ex._gripper_name == "robotiq_2f_85"


@pytest.mark.parametrize("gripper", sorted(GRIPPER_PROFILES))
def test_fully_closed_means_nothing_held(node, gripper):
    ex = make(node, gripper)
    prof = GRIPPER_PROFILES[gripper]
    closed = prof["closed"]
    open_pos = prof.get("open", 0.0)
    ex._latest_joint_state = joint_state(ex._gripper_joint_name, closed)
    assert ex._gripper_fully_closed()
    # halfway back toward open: the fingers stopped on something
    short = closed + 0.5 * (open_pos - closed)
    ex._latest_joint_state = joint_state(ex._gripper_joint_name, short)
    assert not ex._gripper_fully_closed()


def test_hande_open_is_the_wide_position(node):
    ex = make(node, "robotiq_hande")
    assert ex._gripper_joint_name == "robotiq_hande_left_finger_joint"
    ex._latest_joint_state = joint_state(ex._gripper_joint_name, 0.025)
    assert ex._is_at_open(0.025)
    assert not ex._gripper_fully_closed()
    ex._latest_joint_state = joint_state(ex._gripper_joint_name, 0.0)
    assert ex._gripper_fully_closed()
    assert not ex._is_at_open(0.0)


def test_missing_joint_state_never_blocks_a_pick(node):
    ex = make(node, "onrobot_rg2")
    ex._latest_joint_state = None
    assert not ex._gripper_fully_closed()
    ex._latest_joint_state = joint_state("some_other_joint", 1.3)
    assert not ex._gripper_fully_closed()


@pytest.mark.parametrize("gripper", sorted(GRIPPER_PROFILES))
def test_downward_pose_adds_the_tcp_offset(node, gripper):
    ex = make(node, gripper)
    pose = ex._make_downward_pose(0.35, 0.0, 0.10)
    assert pose.pose.position.z == pytest.approx(0.10 + GRIPPER_PROFILES[gripper]["tcp_z"])
    assert (pose.pose.position.x, pose.pose.position.y) == (0.35, 0.0)


@pytest.mark.parametrize("yaw", [0.0, 0.5, -1.2, math.pi / 2])
def test_downward_pose_points_the_tool_down(node, yaw):
    q = make(node, "onrobot_rg2")._make_downward_pose(0.3, 0.0, 0.1, yaw).pose.orientation
    assert q.x ** 2 + q.y ** 2 + q.z ** 2 + q.w ** 2 == pytest.approx(1.0)
    # rotate the tool z axis (0, 0, 1) by the quaternion: its z component is 1 - 2 (x^2 + y^2)
    tool_z_world = 1.0 - 2.0 * (q.x ** 2 + q.y ** 2)
    assert tool_z_world == pytest.approx(-1.0)


def test_yaw_turns_the_fingers(node):
    ex = make(node, "onrobot_rg2")
    q0 = ex._make_downward_pose(0.3, 0.0, 0.1, 0.0).pose.orientation
    q1 = ex._make_downward_pose(0.3, 0.0, 0.1, 0.8).pose.orientation
    # tool x axis in the world: (1 - 2(y^2 + z^2), 2(xy + wz), 2(xz - wy))
    def tool_x(q):
        return (1 - 2 * (q.y ** 2 + q.z ** 2), 2 * (q.x * q.y + q.w * q.z))
    a0, a1 = math.atan2(tool_x(q0)[1], tool_x(q0)[0]), math.atan2(tool_x(q1)[1], tool_x(q1)[0])
    assert abs(a1 - a0) == pytest.approx(0.8, abs=1e-6)


def test_unknown_action_fails(node):
    ex = make(node, "onrobot_rg2")
    assert ex._dispatch_task({"action": "no_such_action"}) is False
    assert ex._dispatch_task({}) is False


def test_server_not_ready_fails(node):
    # the node is never spun and no servers exist, so both clients report not ready
    ex = make(node, "onrobot_rg2")
    assert not ex._move_group_client.server_is_ready()
    assert ex._send_move_group_goal(object(), timeout=0.1) is False
    assert ex.move_to_named_pose("arm", "home") is False
    assert ex._send_gripper_goal(0.0, 10.0, timeout=0.1) is False
    assert ex.wait_for_servers(timeout=0.1) is False
