"""6D pose (position, orientation, size) of one object from its point cloud.

Pure numpy, no ROS. Points are expressed in a frame whose +z is up (base_link). The object is assumed to rest on a
support surface, so its pose has the usual structure: a vertical or horizontal main axis plus a yaw.

    pose = estimate_pose(points_base)       # (N, 3)
    pose["center"], pose["rotation"] (3x3), pose["quaternion"] (x, y, z, w), pose["dims"], pose["shape"],
    pose["standing"], pose["axis"] (unit vector of the main axis), pose["tilt_deg"] (axis vs vertical)

How it decides:
  * PCA of the points gives the principal axes and extents.
  * A "standing" object has its largest extent (or, for a squat object, its height) vertical: the main axis is z.
    The footprint is then fitted with a minimum-area rectangle (yaw) and compared with a circle (shape).
  * A "lying" object (largest extent horizontal, such as a banana or a cylinder on its side) has its main axis in
    the table plane; the yaw is the direction of that axis.
"""
import math
from typing import Dict

import numpy as np


def _min_area_rect(xy: np.ndarray):
    """Minimum-area bounding rectangle of 2D points: (yaw, width, length, centre) with width <= length along yaw."""
    mean = xy.mean(0)
    best = (1e9, 0.0, None)
    for deg in range(0, 90, 2):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        u = (xy[:, 0] - mean[0]) * c + (xy[:, 1] - mean[1]) * s
        v = -(xy[:, 0] - mean[0]) * s + (xy[:, 1] - mean[1]) * c
        area = (u.max() - u.min()) * (v.max() - v.min())
        if area < best[0]:
            best = (area, a, (u.min(), u.max(), v.min(), v.max()))
    _, a, (u0, u1, v0, v1) = best
    c, s = math.cos(a), math.sin(a)
    cu, cv = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
    centre = mean + np.array([c * cu - s * cv, s * cu + c * cv])
    w, l = u1 - u0, v1 - v0
    if w > l:                      # make the long side the second one and rotate the yaw to match
        a += math.pi / 2
        w, l = l, w
    return a % math.pi, w, l, centre


def _circle_rms(xy: np.ndarray) -> float:
    """RMS radial residual of the best-fit circle (algebraic fit)."""
    A = np.c_[2 * xy, np.ones(len(xy))]
    b = (xy ** 2).sum(1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    c, r = sol[:2], math.sqrt(max(sol[2] + sol[0] ** 2 + sol[1] ** 2, 1e-12))
    return float(np.sqrt(np.mean((np.linalg.norm(xy - c, axis=1) - r) ** 2)))


def _rot_z(yaw: float) -> np.ndarray:
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])


def _quat(R: np.ndarray):
    t = np.trace(R)
    if t > 0:
        s = math.sqrt(t + 1) * 2
        return ((R[2, 1] - R[1, 2]) / s, (R[0, 2] - R[2, 0]) / s, (R[1, 0] - R[0, 1]) / s, 0.25 * s)
    i = int(np.argmax(np.diag(R)))
    j, k = (i + 1) % 3, (i + 2) % 3
    s = math.sqrt(1 + R[i, i] - R[j, j] - R[k, k]) * 2
    q = [0.0] * 4
    q[i] = 0.25 * s
    q[j] = (R[j, i] + R[i, j]) / s
    q[k] = (R[k, i] + R[i, k]) / s
    q[3] = (R[k, j] - R[j, k]) / s
    return tuple(q)


def estimate_pose(points: np.ndarray, top_band: float = 0.008) -> Dict:
    """6D pose of the object that `points` (N, 3, +z up) belong to. Needs a reasonably complete top surface."""
    pts = np.asarray(points, dtype=float)
    pts = pts[np.isfinite(pts).all(1)]
    if len(pts) < 30:
        raise ValueError("need at least 30 points")
    mean = pts.mean(0)
    evals, evecs = np.linalg.eigh(np.cov((pts - mean).T))
    order = np.argsort(evals)[::-1]
    evecs = evecs[:, order]
    main = evecs[:, 0]
    main = main if main[2] >= 0 else -main
    tilt = math.degrees(math.acos(min(1.0, abs(main[2]))))
    extents = np.array([np.ptp((pts - mean) @ evecs[:, i]) for i in range(3)])
    height = float(np.ptp(pts[:, 2]))

    horizontal_extent = float(max(np.ptp(pts[:, 0]), np.ptp(pts[:, 1])))
    standing = not (tilt > 60.0 and extents[0] > 1.4 * extents[1] and horizontal_extent > 1.3 * height)

    if standing:
        # footprint from the top surface (the sides are only partly visible from a camera above)
        top = pts[pts[:, 2] > pts[:, 2].max() - top_band][:, :2]
        yaw, w, l, centre = _min_area_rect(top if len(top) >= 10 else pts[:, :2])
        circ = _circle_rms(top if len(top) >= 10 else pts[:, :2])
        box_like = abs(w - l) / max(w, l) > 0.15 or circ > 0.12 * max(w, l)
        shape = "box" if box_like else "cylinder"
        R = _rot_z(yaw if shape == "box" else 0.0)
        z_min = float(pts[:, 2].min())
        centre3 = np.array([centre[0], centre[1], z_min + height / 2])
        dims = (w, l, height) if shape == "box" else (0.5 * (w + l), 0.5 * (w + l), height)
        axis = np.array([0.0, 0.0, 1.0])
    else:
        ax = np.array([main[0], main[1], 0.0])
        ax /= np.linalg.norm(ax)
        yaw = math.atan2(ax[1], ax[0])
        R = _rot_z(yaw)
        local = (pts - mean) @ R
        centre3 = mean + R @ (0.5 * (local.max(0) + local.min(0)))
        dims = tuple(float(x) for x in np.ptp(local, axis=0))
        shape = "lying"
        axis = ax

    return {
        "center": centre3,
        "rotation": R,
        "quaternion": _quat(R),
        "dims": tuple(float(x) for x in dims),
        "shape": shape,
        "standing": bool(standing),
        "axis": axis,
        "tilt_deg": 0.0 if standing else 90.0,
        "yaw": float(math.atan2(R[1, 0], R[0, 0])),
        "pca_axis_tilt_deg": float(tilt),
    }
