"""Collision boxes for a fused cloud or a pose, with no ROS imports."""

from __future__ import annotations

import numpy as np


def axis_aligned_box(points) -> tuple[np.ndarray, np.ndarray] | None:
    """Return (center, size) of the XYZ bounds. Empty input returns None."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] == 0 or pts.shape[1] < 3:
        return None
    xyz = pts[:, :3]
    lo = xyz.min(axis=0)
    hi = xyz.max(axis=0)
    center = (lo + hi) / 2.0
    size = np.maximum(hi - lo, 1e-3)
    return center, size


def box_at_pose(position, size) -> tuple[np.ndarray, np.ndarray]:
    """A box of `size` (x, y, z) whose centre is `position`."""
    center = np.asarray(position, dtype=float).reshape(3)
    dims = np.maximum(np.asarray(size, dtype=float).reshape(3), 1e-3)
    return center, dims
