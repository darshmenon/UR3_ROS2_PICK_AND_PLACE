#!/usr/bin/env python3
"""
cylinder_grasp_detector.py — PCL-free cylinder grasp pose estimator.

Algorithm (centroid + colour filter + RANSAC axis)
───────────────────────────────────────────────────
  1. Decode PointCloud2 → (N,6) array [x, y, z, r, g, b]
  2. Colour filter: keep only points matching the target colour
     (works on clean Gazebo RGBD output; tolerant HSV thresholds)
  3. Z passthrough: keep table-height < z < max_reach
  4. Centroid (cx, cy) = mean of filtered XY
  5. Height extent: grasp_z = cluster min_z + 0.30 * (max_z - min_z)
     (grasp at 30% of cylinder height — reliable friction zone for 2F-85)
  6. Orientation: tool pointing straight down, wrist free (no axis fitting needed
     for symmetric cylinders with parallel-jaw gripper)
  7. Returns GraspCandidate with confidence score

Optional upgrade: replace step 3-5 with RANSAC cylinder model when
ros-humble-pcl-ros is installed.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Optional

import numpy as np

# ── colour targets (HSV) ──────────────────────────────────────────────────────
# Each entry: (h_lo, h_hi, s_lo, v_lo)  all in [0,1] range
COLOUR_HSV: dict[str, tuple] = {
    "red":    ((0.95, 1.0,  0.40, 0.30), (0.0, 0.05, 0.40, 0.30)),  # two hue ranges
    "blue":   ((0.55, 0.72, 0.35, 0.25), None),
    "green":  ((0.28, 0.45, 0.30, 0.25), None),
    "yellow": ((0.12, 0.20, 0.40, 0.40), None),
    "any":    None,   # skip colour filter
}

# ── workspace limits (metres, base_link frame) ───────────────────────────────
Z_TABLE   = 0.00   # anything below this is the floor
Z_MAX     = 0.60   # max object height we care about
XY_RADIUS = 0.55   # only objects within this radius of base_link origin


@dataclass
class GraspCandidate:
    """A single grasp candidate in base_link frame."""
    x: float
    y: float
    grasp_z: float          # z for tool at grasp contact
    pregrasp_z: float       # z for hover before descending
    object_height: float    # estimated cylinder height (m)
    object_radius: float    # estimated cylinder radius (m)
    colour: str
    confidence: float       # 0–1; higher = more points / cleaner cluster
    n_points: int


# ─────────────────────────────────────────────────────────────────────────────

def _rgb_to_hsv(r: np.ndarray, g: np.ndarray, b: np.ndarray):
    """Vectorised RGB [0,1] → HSV [0,1]."""
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    df = mx - mn
    h = np.zeros_like(mx)
    mask = df > 0
    # hue
    mr = mask & (mx == r)
    mg = mask & (mx == g)
    mb = mask & (mx == b)
    h[mr] = (60 * ((g[mr] - b[mr]) / df[mr]) % 360) / 360
    h[mg] = (60 * ((b[mg] - r[mg]) / df[mg] + 2)) / 360
    h[mb] = (60 * ((r[mb] - g[mb]) / df[mb] + 4)) / 360
    s = np.where(mx > 0, df / mx, 0.0)
    v = mx
    return h, s, v


def _colour_mask(rgb: np.ndarray, colour: str) -> np.ndarray:
    """Return boolean mask for points matching the requested colour."""
    if colour == "any" or COLOUR_HSV.get(colour) is None:
        return np.ones(len(rgb), dtype=bool)

    r, g, b = rgb[:, 0] / 255.0, rgb[:, 1] / 255.0, rgb[:, 2] / 255.0
    h, s, v = _rgb_to_hsv(r, g, b)

    ranges = COLOUR_HSV[colour]
    # ranges is a tuple of (h_lo, h_hi, s_lo, v_lo) entries (one or two for red)
    mask = np.zeros(len(rgb), dtype=bool)
    for rng in ranges:
        if rng is None:
            continue
        h_lo, h_hi, s_lo, v_lo = rng
        if h_lo <= h_hi:
            m = (h >= h_lo) & (h <= h_hi) & (s >= s_lo) & (v >= v_lo)
        else:
            # wrapping hue range (e.g. red: 0.95–1.0 ∪ 0.0–0.05)
            m = ((h >= h_lo) | (h <= h_hi)) & (s >= s_lo) & (v >= v_lo)
        mask |= m
    return mask


def decode_pointcloud2(msg) -> Optional[np.ndarray]:
    """
    Decode a sensor_msgs/PointCloud2 → (N, 6) float32 array [x,y,z,r,g,b].
    Returns None if the message has no points.
    """
    try:
        from sensor_msgs_py import point_cloud2 as pc2
    except ImportError:
        raise ImportError("sensor_msgs_py not available — install ros-humble-sensor-msgs-py")

    pts = list(pc2.read_points(msg, field_names=("x", "y", "z", "rgb"), skip_nans=True))
    if not pts:
        return None

    arr = np.array(pts, dtype=np.float32)  # (N,4): x y z rgb_packed
    rgb_packed = arr[:, 3].view(np.uint32)
    r = ((rgb_packed >> 16) & 0xFF).astype(np.float32)
    g = ((rgb_packed >>  8) & 0xFF).astype(np.float32)
    b = ((rgb_packed      ) & 0xFF).astype(np.float32)

    xyz  = arr[:, :3]
    return np.column_stack([xyz, r, g, b])   # (N,6)


def estimate_cylinder_grasp(
    cloud: np.ndarray,
    colour: str = "any",
    pregrasp_offset: float = 0.12,
    min_points: int = 30,
) -> Optional[GraspCandidate]:
    """
    Estimate a grasp pose for a cylinder in the point cloud.

    Args:
        cloud:           (N,6) array [x,y,z,r,g,b] in base_link frame
        colour:          Target colour: "red","blue","green","yellow","any"
        pregrasp_offset: Metres above grasp_z for the hover pose
        min_points:      Minimum cluster points to trust result

    Returns:
        GraspCandidate or None if no object found.
    """
    if cloud is None or len(cloud) == 0:
        return None

    xyz = cloud[:, :3]
    rgb = cloud[:, 3:6].astype(np.uint8)

    # 1. Colour filter
    cmask = _colour_mask(rgb, colour)
    # 2. Z passthrough (remove floor + ceiling)
    zmask = (xyz[:, 2] > Z_TABLE) & (xyz[:, 2] < Z_MAX)
    # 3. XY radius (only workspace area)
    rr = np.sqrt(xyz[:, 0]**2 + xyz[:, 1]**2)
    xymask = rr < XY_RADIUS

    mask = cmask & zmask & xymask
    cluster = xyz[mask]

    if len(cluster) < min_points:
        return None

    # 4. Centroid (horizontal centre of cylinder)
    cx = float(np.mean(cluster[:, 0]))
    cy = float(np.mean(cluster[:, 1]))

    # 5. Height extent
    min_z = float(np.min(cluster[:, 2]))
    max_z = float(np.max(cluster[:, 2]))
    height = max_z - min_z
    if height < 0.02:
        return None   # noise

    grasp_z = min_z + 0.30 * height    # 30% up from bottom

    # 6. Radius estimate (average distance from centroid in XY)
    dx = cluster[:, 0] - cx
    dy = cluster[:, 1] - cy
    radius = float(np.median(np.sqrt(dx**2 + dy**2)))

    # 7. Confidence: normalised point count (cap at 500 pts = 1.0)
    confidence = min(1.0, len(cluster) / 500.0)

    return GraspCandidate(
        x=cx, y=cy,
        grasp_z=grasp_z,
        pregrasp_z=grasp_z + pregrasp_offset,
        object_height=height,
        object_radius=radius,
        colour=colour,
        confidence=confidence,
        n_points=len(cluster),
    )
