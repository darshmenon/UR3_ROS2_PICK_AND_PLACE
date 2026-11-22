"""Offline checks for the fused-cloud box and a known hand-eye shift."""

import numpy as np
import pytest

cv2 = pytest.importorskip("cv2")

from ur_perception.scene_geometry import axis_aligned_box, box_at_pose


def test_fused_cloud_box_is_the_point_bounds():
    cloud = np.array([
        [0.0, 0.0, 0.0],
        [0.10, 0.04, 0.08],
        [0.02, -0.02, 0.01],
    ])
    center, size = axis_aligned_box(cloud)
    assert center == pytest.approx([0.05, 0.01, 0.04])
    assert size == pytest.approx([0.10, 0.06, 0.08])
    assert axis_aligned_box(np.zeros((0, 3))) is None


def test_pose_box_uses_the_given_centre():
    center, size = box_at_pose((0.3, -0.1, 0.05), (0.04, 0.04, 0.1))
    assert center == pytest.approx([0.3, -0.1, 0.05])
    assert size == pytest.approx([0.04, 0.04, 0.1])


def _pose(R, t):
    return R.astype(np.float64), np.asarray(t, dtype=np.float64).reshape(3, 1)


def test_handeye_recovers_a_known_camera_shift():
    """Eye-in-hand: shift the camera on the gripper by 3 cm and check the solve."""
    def rot(axis, angle):
        r, _ = cv2.Rodrigues(np.asarray(axis, dtype=np.float64) * angle)
        return r

    true_R, true_t = _pose(rot((0, 1, 0), 0.4), (0.02, -0.01, 0.05))
    board_R, board_t = _pose(np.eye(3), (0.4, 0.0, 0.0))
    grips_R, grips_t, cams_R, cams_t = [], [], [], []
    for i in range(8):
        gR = rot((0, 0, 1), 0.2 * i) @ rot((1, 0, 0), 0.15 * np.sin(i))
        gt = np.array([[0.3 + 0.01 * i], [0.02 * np.cos(i)], [0.2]])
        # target in camera = X^-1 * gripper^-1 * board
        g_inv_R = gR.T
        g_inv_t = -gR.T @ gt
        base_R = g_inv_R @ board_R
        base_t = g_inv_R @ board_t + g_inv_t
        cR = true_R.T @ base_R
        ct = true_R.T @ (base_t - true_t)
        grips_R.append(gR)
        grips_t.append(gt)
        cams_R.append(cR)
        cams_t.append(ct)

    got_R, got_t = cv2.calibrateHandEye(
        grips_R, grips_t, cams_R, cams_t, method=cv2.CALIB_HAND_EYE_PARK
    )
    assert got_t.reshape(3) == pytest.approx(true_t.reshape(3), abs=1e-6)

    shift = np.array([[0.03], [0.0], [0.0]])
    shifted_t = true_t + shift
    cams_R2, cams_t2 = [], []
    for gR, gt in zip(grips_R, grips_t):
        g_inv_R = gR.T
        g_inv_t = -gR.T @ gt
        base_R = g_inv_R @ board_R
        base_t = g_inv_R @ board_t + g_inv_t
        cams_R2.append(true_R.T @ base_R)
        cams_t2.append(true_R.T @ (base_t - shifted_t))
    _, shifted = cv2.calibrateHandEye(
        grips_R, grips_t, cams_R2, cams_t2, method=cv2.CALIB_HAND_EYE_PARK
    )
    assert (shifted - got_t).reshape(3) == pytest.approx(shift.reshape(3), abs=1e-5)
