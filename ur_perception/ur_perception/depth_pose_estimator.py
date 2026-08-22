"""
Depth-based 3D pose estimator.

Given a pixel location, a depth image, and camera intrinsics, computes the
3D position of a detected object in the camera frame.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any

from geometry_msgs.msg import PoseStamped, Pose, Point, Quaternion


class DepthPoseEstimator:
    """
    Project 2D pixel detections into 3D camera-frame poses using depth images.

    Parameters
    ----------
    fx, fy : float
        Focal lengths in pixels.
    cx, cy : float
        Principal point in pixels.
    depth_scale : float
        Multiply raw depth pixel value by this to get meters.
        - RealSense D435 depth images are in millimetres → depth_scale = 0.001
        - Some drivers publish in metres  → depth_scale = 1.0
    patch_radius : int
        Half-side of the square patch (pixels) sampled around the centroid when
        estimating depth. Median of the valid pixels in the patch is used.
    """

    def __init__(
        self,
        fx: float,
        fy: float,
        cx: float,
        cy: float,
        depth_scale: float = 0.001,
        patch_radius: int = 5,
    ) -> None:
        self._fx = float(fx)
        self._fy = float(fy)
        self._cx = float(cx)
        self._cy = float(cy)
        self._depth_scale = float(depth_scale)
        self._patch_radius = max(1, int(patch_radius))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def pixel_to_3d(
        self,
        u: int,
        v: int,
        depth_image: np.ndarray,
        min_depth_m: float = 0.05,
        max_depth_m: float = 2.0,
    ) -> Optional[Tuple[float, float, float]]:
        """
        Back-project a pixel (u, v) to a 3D point in the camera frame.

        A small square patch centred on (u, v) is sampled.  Valid depth pixels
        (non-zero, within [min_depth_m, max_depth_m]) are collected and their
        median is taken to reduce noise from holes and outliers.

        Parameters
        ----------
        u, v : int
            Pixel column (u) and row (v).
        depth_image : np.ndarray
            Depth image (H x W), dtype uint16 or float32.
            Raw values are multiplied by ``depth_scale`` to convert to metres.
        min_depth_m, max_depth_m : float
            Depth values outside this range are treated as invalid.

        Returns
        -------
        (x, y, z) in metres in the camera frame, or None if no valid depth.
        """
        h, w = depth_image.shape[:2]
        r = self._patch_radius

        v0 = max(0, v - r)
        v1 = min(h - 1, v + r)
        u0 = max(0, u - r)
        u1 = min(w - 1, u + r)

        patch = depth_image[v0:v1 + 1, u0:u1 + 1].astype(np.float64)
        depths_m = patch * self._depth_scale

        # Filter out invalid / out-of-range depth values
        valid = depths_m[(depths_m > min_depth_m) & (depths_m < max_depth_m)]
        if valid.size == 0:
            return None

        z = float(np.median(valid))

        # Pin-hole back-projection
        x = (u - self._cx) * z / self._fx
        y = (v - self._cy) * z / self._fy

        return (x, y, z)

    def estimate_object_pose(
        self,
        centroid_px: Tuple[int, int],
        bbox: Tuple[int, int, int, int],
        depth_image: np.ndarray,
        label: str,
        frame_id: str = 'camera_head_link',
        stamp=None,
        min_depth_m: float = 0.05,
        max_depth_m: float = 2.0,
    ) -> Optional[PoseStamped]:
        """
        Estimate the 6-DOF pose of a detected object in the camera frame.

        The object is assumed to be sitting flat on a horizontal surface (the
        orientation quaternion is therefore identity — a downstream node can
        refine this using the gripper approach direction).

        Parameters
        ----------
        centroid_px : (u, v)
            Pixel centroid of the detection (column, row).
        bbox : (x, y, w, h)
            Bounding box in pixels (not used for depth, kept for future use).
        depth_image : np.ndarray
            Depth image aligned to the colour frame.
        label : str
            Object class / color label (not used directly here).
        frame_id : str
            TF frame that the returned pose is expressed in.
        stamp : rclpy.time.Time or None
            ROS timestamp to attach to the pose header.
        min_depth_m, max_depth_m : float
            Valid depth range in metres.

        Returns
        -------
        geometry_msgs.msg.PoseStamped in the camera frame, or None.
        """
        u, v = int(centroid_px[0]), int(centroid_px[1])
        point_3d = self.pixel_to_3d(u, v, depth_image, min_depth_m, max_depth_m)

        if point_3d is None:
            return None

        x, y, z = point_3d

        pose_stamped = PoseStamped()
        pose_stamped.header.frame_id = frame_id
        if stamp is not None:
            pose_stamped.header.stamp = stamp

        pose_stamped.pose.position = Point(x=x, y=y, z=z)
        # Identity orientation — object is assumed upright / approach from above.
        pose_stamped.pose.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)

        return pose_stamped

    def bbox_size_m(
        self,
        bbox: Tuple[int, int, int, int],
        z_m: float,
    ) -> Tuple[float, float]:
        """
        Approximate the real-world (width, height) of a bounding box.

        Pinhole similar triangles: a pixel span subtends
        ``pixels * z / focal_length`` metres at depth ``z``. Used to size
        planning-scene collision objects per-detection instead of a single
        hardcoded guess for every object.

        Parameters
        ----------
        bbox : (x, y, w, h) in pixels.
        z_m : depth of the object (metres), e.g. from ``pixel_to_3d``.

        Returns
        -------
        (width_m, height_m)
        """
        _, _, w_px, h_px = bbox
        width_m = (w_px * z_m) / self._fx
        height_m = (h_px * z_m) / self._fy
        return width_m, height_m

    # ------------------------------------------------------------------
    # Properties (read-only)
    # ------------------------------------------------------------------

    @property
    def intrinsics(self) -> Dict[str, float]:
        return {
            'fx': self._fx,
            'fy': self._fy,
            'cx': self._cx,
            'cy': self._cy,
            'depth_scale': self._depth_scale,
        }
