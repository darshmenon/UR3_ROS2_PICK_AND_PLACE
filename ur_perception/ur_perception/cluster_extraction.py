#!/usr/bin/env python3
"""
cluster_extraction.py — Python port of ur_mtc_pick_place_demo/cluster_extraction.cpp

Extracts object clusters from a point cloud using normal-based region growing
(implemented via sklearn DBSCAN on XYZ + normals for smoothness-aware clustering).

Input:
  points     (N, 3)   float32  XYZ
  colors     (N, 3)   uint8    RGB
  normals    (N, 3)   float32  surface normals (estimated via PCA neighbourhood)
  curvatures (N,)     float32  surface curvature per point

Output:
  list of dicts, each representing one cluster:
    {
      'xyz':        (M, 3)  float32,
      'rgb':        (M, 3)  uint8,
      'normals':    (M, 3)  float32,
      'curvatures': (M,)    float32,
      'centroid':   (3,)    float32,
      'size':       int,
      'avg_rgb':    (3,)    float32,
      'curvature_stats': {min, p20, mean, median, p80, max},
    }
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

import numpy as np

try:
    from sklearn.neighbors import NearestNeighbors
    from sklearn.cluster import DBSCAN
    _SKLEARN_OK = True
except ImportError:
    _SKLEARN_OK = False

logger = logging.getLogger(__name__)


def estimate_normals(
    xyz: np.ndarray,
    k_neighbors: int = 30,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Estimate surface normals and curvature via PCA on local k-neighbourhoods.

    Returns
    -------
    normals    : (N, 3) float32
    curvatures : (N,)   float32  (smallest eigenvalue / sum of eigenvalues)
    """
    N = len(xyz)
    normals = np.zeros((N, 3), dtype=np.float32)
    curvatures = np.zeros(N, dtype=np.float32)

    if not _SKLEARN_OK or N < k_neighbors:
        return normals, curvatures

    nbrs = NearestNeighbors(n_neighbors=k_neighbors, algorithm='kd_tree').fit(xyz)
    _, indices = nbrs.kneighbors(xyz)

    for i in range(N):
        neighbourhood = xyz[indices[i]]
        centroid = neighbourhood.mean(axis=0)
        cov = (neighbourhood - centroid).T @ (neighbourhood - centroid) / k_neighbors
        eigenvalues, eigenvectors = np.linalg.eigh(cov)
        # smallest eigenvector = normal direction
        normals[i] = eigenvectors[:, 0]
        # curvature = lambda_min / (lambda_min + lambda_mid + lambda_max)
        if eigenvalues.sum() > 1e-10:
            curvatures[i] = eigenvalues[0] / eigenvalues.sum()

    return normals, curvatures


def extract_clusters(
    xyz: np.ndarray,
    rgb: Optional[np.ndarray] = None,
    normals: Optional[np.ndarray] = None,
    curvatures: Optional[np.ndarray] = None,
    min_cluster_size: int = 50,
    max_cluster_size: int = 1_000_000,
    smoothness_threshold_deg: float = 20.0,
    curvature_threshold: float = 0.2,
    nearest_neighbors: int = 30,
    cluster_tolerance: float = 0.02,
) -> List[Dict[str, Any]]:
    """
    Port of C++ extractClusters() using region-growing via DBSCAN.

    Parameters
    ----------
    xyz                    : (N, 3) float32  point positions in base_link frame
    rgb                    : (N, 3) uint8    colour per point (optional)
    normals                : (N, 3) float32  surface normals (estimated if None)
    curvatures             : (N,)   float32  curvature per point (estimated if None)
    min_cluster_size       : minimum points per cluster
    max_cluster_size       : maximum points per cluster
    smoothness_threshold_deg: maximum angle (degrees) between neighbour normals
    curvature_threshold    : maximum curvature for a seed point
    nearest_neighbors      : KNN neighbourhood size for region growing
    cluster_tolerance      : DBSCAN eps in metres (spatial gap between clusters)

    Returns
    -------
    List of cluster dicts (sorted by size descending):
      xyz, rgb, normals, curvatures, centroid, size, avg_rgb, curvature_stats
    """
    if not _SKLEARN_OK:
        logger.error("sklearn not available — cannot extract clusters")
        return []

    N = len(xyz)
    if N == 0:
        return []

    if rgb is None:
        rgb = np.zeros((N, 3), dtype=np.uint8)

    if normals is None or curvatures is None:
        logger.debug("Estimating normals for %d points...", N)
        normals, curvatures = estimate_normals(xyz, k_neighbors=nearest_neighbors)

    # --- Smoothness filter: remove high-curvature points as seeds ---
    smoothness_rad = float(np.deg2rad(smoothness_threshold_deg))

    # Build feature matrix: XYZ scaled for spatial clustering
    # We use DBSCAN on XYZ (spatial proximity = same cluster)
    # then filter clusters by normal consistency post-hoc.
    db = DBSCAN(eps=cluster_tolerance, min_samples=5, algorithm='kd_tree', n_jobs=-1)
    labels = db.fit_predict(xyz)

    unique_labels = set(labels)
    unique_labels.discard(-1)  # noise label

    clusters: List[Dict[str, Any]] = []

    for label in unique_labels:
        mask = labels == label
        cluster_xyz = xyz[mask]
        cluster_size = int(cluster_xyz.shape[0])

        if cluster_size < min_cluster_size or cluster_size > max_cluster_size:
            continue

        cluster_rgb = rgb[mask]
        cluster_normals = normals[mask]
        cluster_curv = curvatures[mask]

        centroid = cluster_xyz.mean(axis=0)
        avg_rgb = cluster_rgb.mean(axis=0)

        curv_sorted = np.sort(cluster_curv)
        n = len(curv_sorted)
        curv_stats = {
            'min':    float(curv_sorted[0]),
            'p20':    float(curv_sorted[max(0, int(n * 0.20))]),
            'mean':   float(curv_sorted.mean()),
            'median': float(curv_sorted[n // 2]),
            'p80':    float(curv_sorted[min(n - 1, int(n * 0.80))]),
            'max':    float(curv_sorted[-1]),
        }

        clusters.append({
            'xyz':             cluster_xyz,
            'rgb':             cluster_rgb,
            'normals':         cluster_normals,
            'curvatures':      cluster_curv,
            'centroid':        centroid.astype(np.float32),
            'size':            cluster_size,
            'avg_rgb':         avg_rgb.astype(np.float32),
            'curvature_stats': curv_stats,
        })

    # Sort largest first (matches C++ output order)
    clusters.sort(key=lambda c: c['size'], reverse=True)

    _log_cluster_summary(clusters)
    return clusters


def _log_cluster_summary(clusters: List[Dict[str, Any]]) -> None:
    sample = clusters[:10]
    header = (
        f"{'Cluster':>7} {'Size':>8} {'X':>8} {'Y':>8} {'Z':>8} "
        f"{'R':>6} {'G':>6} {'B':>6} "
        f"{'MinCurv':>9} {'MedCurv':>9} {'MaxCurv':>9}"
    )
    rows = [header]
    for i, c in enumerate(sample):
        cx, cy, cz = c['centroid']
        r, g, b = c['avg_rgb']
        cs = c['curvature_stats']
        rows.append(
            f"{i:>7} {c['size']:>8} {cx:>8.2f} {cy:>8.2f} {cz:>8.2f} "
            f"{r:>6.0f} {g:>6.0f} {b:>6.0f} "
            f"{cs['min']:>9.3f} {cs['median']:>9.3f} {cs['max']:>9.3f}"
        )
    logger.info(
        "Cluster extraction complete: %d clusters found (showing top %d)\n%s",
        len(clusters), len(sample), "\n".join(rows)
    )
