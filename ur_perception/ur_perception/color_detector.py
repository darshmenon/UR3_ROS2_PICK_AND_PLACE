"""
HSV color-based object detector.

Detects colored objects in a BGR image by thresholding in HSV color space.
Supported colors: red, green, blue, yellow, orange.
"""

import cv2
import numpy as np
from typing import List, Dict, Any


# HSV color ranges for each supported color.
# Format: list of (lower, upper) tuples in HSV space (H: 0-179, S: 0-255, V: 0-255).
# Red wraps around the hue wheel, so two ranges are needed.
_COLOR_RANGES: Dict[str, List[tuple]] = {
    'red': [
        (np.array([0,   120,  70], dtype=np.uint8), np.array([10,  255, 255], dtype=np.uint8)),
        (np.array([170, 120,  70], dtype=np.uint8), np.array([179, 255, 255], dtype=np.uint8)),
    ],
    'green': [
        (np.array([36,  80,  50], dtype=np.uint8), np.array([86,  255, 255], dtype=np.uint8)),
    ],
    'blue': [
        (np.array([94,  80,  50], dtype=np.uint8), np.array([126, 255, 255], dtype=np.uint8)),
    ],
    'yellow': [
        (np.array([20,  100, 100], dtype=np.uint8), np.array([35,  255, 255], dtype=np.uint8)),
    ],
    'orange': [
        (np.array([10,  100, 100], dtype=np.uint8), np.array([20,  255, 255], dtype=np.uint8)),
    ],
}

# Representative BGR colors for visualization (used to draw bounding boxes)
_COLOR_BGR: Dict[str, tuple] = {
    'red':    (0,   0,   255),
    'green':  (0,   255, 0),
    'blue':   (255, 0,   0),
    'yellow': (0,   255, 255),
    'orange': (0,   165, 255),
}

# Representative (r, g, b) floats 0-1 for each color label
_COLOR_RGB_FLOAT: Dict[str, tuple] = {
    'red':    (1.0, 0.0, 0.0),
    'green':  (0.0, 1.0, 0.0),
    'blue':   (0.0, 0.0, 1.0),
    'yellow': (1.0, 1.0, 0.0),
    'orange': (1.0, 0.647, 0.0),
}

# Minimum contour area in pixels to suppress tiny detections
_MIN_CONTOUR_AREA = 500


class ColorDetector:
    """
    Detect objects by HSV color segmentation.

    Parameters
    ----------
    target_colors : list[str] or None
        Subset of colors to detect. If None, all supported colors are used.
    min_area : int
        Minimum bounding-box area (pixels²) for a detection to be kept.
    """

    SUPPORTED_COLORS = list(_COLOR_RANGES.keys())

    def __init__(
        self,
        target_colors: List[str] | None = None,
        min_area: int = _MIN_CONTOUR_AREA,
    ) -> None:
        if target_colors is None:
            self._colors = self.SUPPORTED_COLORS
        else:
            unknown = set(target_colors) - set(self.SUPPORTED_COLORS)
            if unknown:
                raise ValueError(f"Unsupported colors requested: {unknown}. "
                                 f"Supported: {self.SUPPORTED_COLORS}")
            self._colors = list(target_colors)

        self._min_area = max(1, min_area)

        # Pre-build morphological kernel
        self._kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, bgr_image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect colored objects in a BGR image.

        Parameters
        ----------
        bgr_image : np.ndarray
            Input image in BGR format (as returned by cv2.imread or cv_bridge).

        Returns
        -------
        list[dict]
            Each dict has:
            - label        : str          - color name
            - bbox         : (x, y, w, h) - bounding box in pixels
            - centroid_px  : (u, v)       - centroid in pixels (column, row)
            - confidence   : float        - 0-1, based on fill ratio of convex hull
            - color_rgb    : (r, g, b)    - float 0-1 representative color
            - mask         : np.ndarray   - binary mask (same HxW as input), uint8
        """
        if bgr_image is None or bgr_image.size == 0:
            return []

        hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)
        detections: List[Dict[str, Any]] = []

        for color_name in self._colors:
            mask = self._build_mask(hsv, color_name)
            blobs = self._extract_blobs(mask)
            for blob in blobs:
                x, y, w, h = blob['bbox']
                area = blob['area']
                hull_area = blob['hull_area']
                confidence = float(area / hull_area) if hull_area > 0 else 0.0
                confidence = min(1.0, confidence)

                cx = x + w // 2
                cy = y + h // 2

                detections.append({
                    'label':       color_name,
                    'bbox':        (x, y, w, h),
                    'centroid_px': (cx, cy),
                    'confidence':  confidence,
                    'color_rgb':   _COLOR_RGB_FLOAT[color_name],
                    'mask':        blob['mask'],
                })

        return detections

    def draw_detections(
        self,
        bgr_image: np.ndarray,
        detections: List[Dict[str, Any]],
    ) -> np.ndarray:
        """
        Draw bounding boxes and labels on a copy of the input image.

        Returns
        -------
        np.ndarray
            Annotated BGR image.
        """
        vis = bgr_image.copy()
        for det in detections:
            color_name = det['label']
            x, y, w, h = det['bbox']
            cx, cy = det['centroid_px']
            conf = det['confidence']
            bgr = _COLOR_BGR.get(color_name, (200, 200, 200))

            cv2.rectangle(vis, (x, y), (x + w, y + h), bgr, 2)
            cv2.circle(vis, (cx, cy), 4, bgr, -1)

            label_text = f"{color_name} {conf:.2f}"
            cv2.putText(
                vis, label_text, (x, max(0, y - 6)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, bgr, 2, cv2.LINE_AA,
            )
        return vis

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_mask(self, hsv: np.ndarray, color_name: str) -> np.ndarray:
        """Return a binary mask for the given color."""
        ranges = _COLOR_RANGES[color_name]
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for lower, upper in ranges:
            mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))

        # Clean up noise
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  self._kernel, iterations=1)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self._kernel, iterations=2)
        return mask

    def _extract_blobs(self, mask: np.ndarray) -> List[Dict[str, Any]]:
        """Extract individual blobs from a binary mask."""
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        blobs = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < self._min_area:
                continue

            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)

            x, y, w, h = cv2.boundingRect(cnt)

            # Build a per-blob mask (same size as full image mask)
            blob_mask = np.zeros_like(mask)
            cv2.drawContours(blob_mask, [cnt], -1, 255, thickness=cv2.FILLED)

            blobs.append({
                'bbox':      (x, y, w, h),
                'area':      area,
                'hull_area': hull_area,
                'mask':      blob_mask,
            })

        return blobs
