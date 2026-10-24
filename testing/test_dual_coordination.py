"""Offline tests (no sim) for the dual-arm whole-body controller in ur_dual_coordination.

    source install/setup.bash && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /usr/bin/python3 -m pytest testing/test_dual_coordination.py -q
"""
import subprocess
import sys
from pathlib import Path

import numpy as np
import pinocchio as pin
import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "ur_dual_coordination"))

from ur_dual_coordination.controller import ControllerConfig, DualArmController, reach_poses  # noqa: E402
from ur_dual_coordination.kinematics import DualArm  # noqa: E402


@pytest.fixture(scope="module")
def dual():
    xml = subprocess.run(["xacro", str(REPO / "moveit_config/config/dual_ur.urdf.xacro"), "gripper:=robotiq_2f_85"],
                         capture_output=True, text=True, check=True).stdout
    return DualArm(xml)


def facing_poses(x=0.20, z=0.25, half_gap=0.06):
    """Left hand looks toward -y, right hand toward +y, both at the same x, z, half_gap either side of y = 0."""
    left = pin.SE3(np.column_stack([[1, 0, 0], np.cross([0, -1, 0], [1, 0, 0]), [0, -1, 0]]), np.array([x, half_gap, z]))
    right = pin.SE3(np.column_stack([[1, 0, 0], np.cross([0, 1, 0], [1, 0, 0]), [0, 1, 0]]), np.array([x, -half_gap, z]))
    return left, right


@pytest.fixture(scope="module")
def meeting_q(dual):
    q0 = dual.q_from_dict({f"{s}_{j}": v for s in ("left", "right") for j, v in (
        ("shoulder_lift_joint", -1.2), ("elbow_joint", 1.6), ("wrist_1_joint", -1.9), ("wrist_2_joint", -1.57))})
    left, right = facing_poses()
    q, el, er = reach_poses(dual, q0, left, right)
    assert el < 1e-3 and er < 1e-3, "the two hands could not both reach the meeting point"
    return q


def carry(dual, q0, delta_p, delta_yaw=0.0, config=None, T=4.0, dt=0.01):
    ctl = DualArmController(dual, config or ControllerConfig(max_joint_speed=5.0, damping=0.002))
    q = q0.copy()
    ctl.set_grasp(q)
    start = ctl.object_pose(q)
    goal_rot = pin.exp3(delta_yaw * np.array([0, 0, 1.0])) @ start.rotation
    goal_p = start.translation + np.asarray(delta_p)
    worst_hand = 0.0
    min_dist, limits = 9.0, set()
    for i in range(int(T / dt)):
        t = (i + 1) / int(T / dt)
        s = 10 * t ** 3 - 15 * t ** 4 + 6 * t ** 5
        target = pin.SE3(pin.exp3(s * delta_yaw * np.array([0, 0, 1.0])) @ start.rotation,
                         start.translation + s * np.asarray(delta_p))
        st = ctl.step(q, target, dt=dt)
        q = st.q
        dual.update(q)
        lMr = dual.placement(dual.tool["left"]).inverse() * dual.placement(dual.tool["right"])
        worst_hand = max(worst_hand, np.linalg.norm((ctl.lMr_des.inverse() * lMr).translation))
        min_dist = min(min_dist, st.min_distance)
        limits |= set(st.saturated)
    end = ctl.object_pose(q)
    pos_err = np.linalg.norm(end.translation - goal_p)
    rot_err = np.linalg.norm(pin.log3(goal_rot.T @ end.rotation))
    return pos_err, rot_err, worst_hand, min_dist, limits, q


def test_model_is_two_six_joint_arms(dual):
    assert dual.nv == 12 and len(dual.joint_names) == 12
    dual.update(np.zeros(12))
    left, right = dual.placement(dual.tool["left"]).translation, dual.placement(dual.tool["right"]).translation
    assert left[1] > 0 > right[1], "left arm is on +y, right arm on -y"


@pytest.mark.parametrize("delta_p, yaw", [([0, 0, 0.06], 0.0), ([0.06, 0, 0], 0.0), ([0, 0.06, 0], 0.0),
                                          ([0.04, 0.03, 0.04], np.radians(15))])
def test_object_reaches_target_and_hands_stay_rigid(dual, meeting_q, delta_p, yaw):
    pos_err, rot_err, worst_hand, min_dist, limits, _ = carry(dual, meeting_q, delta_p, yaw)
    assert pos_err < 0.003, f"object {1000 * pos_err:.1f} mm from its target"
    assert rot_err < np.radians(1.0)
    assert worst_hand < 0.001, f"hands drifted {1000 * worst_hand:.2f} mm apart: the object would be squeezed or dropped"
    assert min_dist >= 0.10, "arms came too close to each other"
    assert not limits, f"joint limits hit: {limits}"


def test_unreachable_target_stays_inside_joint_limits(dual, meeting_q):
    _, _, worst_hand, _, _, q = carry(dual, meeting_q, [0.0, 0.0, 1.5], T=2.0)
    assert np.all(np.isfinite(q))
    assert np.all(q >= dual.lower) and np.all(q <= dual.upper)


def test_arms_pushed_apart_when_too_close(dual, meeting_q):
    """Hands 4 cm apart (a small object): the avoidance row must not let the closest points get any closer."""
    left, right = facing_poses(half_gap=0.02)
    q0 = dual.q_from_dict({f"{s}_{j}": v for s in ("left", "right") for j, v in (
        ("shoulder_lift_joint", -1.2), ("elbow_joint", 1.6), ("wrist_1_joint", -1.9), ("wrist_2_joint", -1.57))})
    q, el, er = reach_poses(dual, q0, left, right)
    assert el < 1e-3 and er < 1e-3
    start = dual.min_arm_distance(q)
    *_, min_dist, _, _ = carry(dual, q, [0.0, 0.0, 0.05], T=2.0)
    assert min_dist > start - 0.01


def test_object_reaches_targets_with_a_lagging_arm(dual, meeting_q):
    """The real arm trails its command (controller lag). Model it as a first-order lag and run the same logic as
    the node (integrate our own command, resync only if the arm lags more than 0.35 rad): every move must still
    land within 1 mm, including the faster return to the start that stalled 29 mm short in the simulator."""
    ctl = DualArmController(dual, ControllerConfig(max_joint_speed=1.0))
    q = meeting_q.copy()
    ctl.set_grasp(q)
    q_cmd, dt, tau = q.copy(), 0.02, 0.4
    start_p = ctl.object_pose(q).translation.copy()
    cur = start_p.copy()
    for move in ([0, 0, 0.06], [0.06, 0, 0], [0, 0.06, 0], "back"):
        goal = start_p if move == "back" else cur + np.array(move)
        start = ctl.object_pose(q)
        dur = max(1.5, np.linalg.norm(goal - start.translation) / 0.05)
        t = 0.0
        while t < dur + 6.0:
            s = min(1.0, t / dur)
            s = 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5
            target = pin.SE3(start.rotation, start.translation + s * (goal - start.translation))
            if np.max(np.abs(q_cmd - q)) > 0.35:
                q_cmd = q.copy()
            q_cmd = ctl.step(q_cmd, target, dt=dt).q
            q = q + (q_cmd - q) * (1 - np.exp(-dt / tau))
            t += dt
        cur = ctl.object_pose(q).translation
        assert np.linalg.norm(cur - goal) < 0.001, f"{move}: {1000 * np.linalg.norm(cur - goal):.1f} mm from the goal"
