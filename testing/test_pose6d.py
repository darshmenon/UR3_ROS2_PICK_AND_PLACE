"""Offline tests for ur_perception.pose6d (no ROS, no sim)."""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ur_perception"))
from ur_perception.pose6d import estimate_pose  # noqa: E402

RNG = np.random.default_rng(0)


def yaw_err(a, b, period):
    d = (a - b) % period
    return min(d, period - d)


def box_cloud(cx, cy, yaw, w, l, h, n=1500, sides=True):
    """Points on the top face and the two faces a camera in front would see, in the box frame then rotated by yaw."""
    top = np.c_[RNG.uniform(-w / 2, w / 2, n), RNG.uniform(-l / 2, l / 2, n), np.full(n, h)]
    parts = [top]
    if sides:
        m = n // 2
        parts.append(np.c_[np.full(m, -w / 2), RNG.uniform(-l / 2, l / 2, m), RNG.uniform(0, h, m)])
        parts.append(np.c_[RNG.uniform(-w / 2, w / 2, m), np.full(m, -l / 2), RNG.uniform(0, h, m)])
    p = np.vstack(parts)
    c, s = math.cos(yaw), math.sin(yaw)
    return np.c_[c * p[:, 0] - s * p[:, 1] + cx, s * p[:, 0] + c * p[:, 1] + cy, p[:, 2] + 1.04]


@pytest.mark.parametrize("yaw_deg", [0, 30, 60, 100, 145])
def test_box_yaw_and_centre(yaw_deg):
    yaw = math.radians(yaw_deg)
    p = estimate_pose(box_cloud(0.35, -0.05, yaw, 0.04, 0.09, 0.05))
    assert p["standing"] and p["shape"] == "box"
    assert yaw_err(p["yaw"], yaw, math.pi) < math.radians(4)
    assert np.hypot(p["center"][0] - 0.35, p["center"][1] + 0.05) < 0.006
    assert abs(p["dims"][2] - 0.05) < 0.004


def test_standing_cylinder():
    n = 2500
    a = RNG.uniform(0, 2 * math.pi, n)
    r = 0.025
    top = np.c_[0.3 + r * np.sqrt(RNG.uniform(0, 1, n)) * np.cos(a), 0.1 + r * np.sqrt(RNG.uniform(0, 1, n)) * np.sin(a)]
    side_a = RNG.uniform(math.pi, 2 * math.pi, n // 2)
    side = np.c_[0.3 + r * np.cos(side_a), 0.1 + r * np.sin(side_a), RNG.uniform(0, 0.08, n // 2) + 1.04]
    pts = np.vstack([np.c_[top, np.full(n, 1.04 + 0.08)], side])
    p = estimate_pose(pts)
    assert p["standing"] and p["shape"] == "cylinder"
    assert np.hypot(p["center"][0] - 0.3, p["center"][1] - 0.1) < 0.008
    assert abs(p["dims"][0] - 0.05) < 0.006


def test_lying_cylinder_yaw():
    yaw = math.radians(40)
    n = 3000
    t = RNG.uniform(-0.06, 0.06, n)
    a = RNG.uniform(0, math.pi, n)            # upper half only: what a camera above sees
    r = 0.02
    local = np.c_[t, r * np.cos(a), r + r * np.sin(a)]
    c, s = math.cos(yaw), math.sin(yaw)
    pts = np.c_[c * local[:, 0] - s * local[:, 1] + 0.35, s * local[:, 0] + c * local[:, 1] + 0.0, local[:, 2] + 1.04]
    p = estimate_pose(pts)
    assert not p["standing"] and p["shape"] == "lying"
    assert yaw_err(p["yaw"], yaw, math.pi) < math.radians(5)
    assert abs(p["dims"][0] - 0.12) < 0.01


def test_quaternion_is_unit_and_matches_rotation():
    p = estimate_pose(box_cloud(0.3, 0.0, math.radians(50), 0.05, 0.08, 0.05))
    x, y, z, w = p["quaternion"]
    assert abs(math.sqrt(x * x + y * y + z * z + w * w) - 1) < 1e-6
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    assert np.allclose(R, p["rotation"], atol=1e-6)


def test_too_few_points():
    with pytest.raises(ValueError):
        estimate_pose(np.zeros((5, 3)))


CAPTURE = Path(__file__).resolve().parent / "_out" / "gn_cyl.npz"


@pytest.mark.skipif(not CAPTURE.exists(), reason="needs the sim capture from graspnet_check.py")
def test_real_capture_cylinder():
    d = np.load(CAPTURE)
    depth, K, seg, T = d["depth"], d["K"], d["segmap"], d["T_base_cam"]
    if "optical" not in d.files:
        T = T @ np.array([[0, 0, 1, 0], [-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)
    v, u = np.nonzero((seg > 0) & np.isfinite(depth) & (depth > 0.1) & (depth < 2.0))
    z = depth[v, u]
    cam = np.c_[(u - K[0, 2]) * z / K[0, 0], (v - K[1, 2]) * z / K[1, 1], z, np.ones_like(z)]
    base = (T @ cam.T).T[:, :3]
    p = estimate_pose(base)
    truth = d["truth"]
    assert p["standing"]
    assert np.hypot(p["center"][0] - truth[0], p["center"][1] - truth[1]) < 0.03
