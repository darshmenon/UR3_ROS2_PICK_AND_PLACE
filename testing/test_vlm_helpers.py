"""Offline tests for the VLM node's pure helpers (parse_bbox, fit_size). Needs the ROS env sourced (imports rclpy)."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ur_perception"))
from ur_perception.vlm_grounding_node import _PATCH, fit_size, parse_bbox  # noqa: E402


def test_plain_json():
    assert parse_bbox("[10, 20, 110, 220]") == (10, 20, 110, 220)


def test_fenced_json_and_prose():
    assert parse_bbox('```json\n{"bbox_2d": [1.5, 2, 30, 40.5]}\n```') == (1.5, 2, 30, 40.5)
    assert parse_bbox("The cube is at [5,6,50,60] in the image") == (5, 6, 50, 60)


def test_skips_degenerate_box_takes_next():
    assert parse_bbox("[50, 50, 10, 10] then [1, 1, 9, 9]") == (1, 1, 9, 9)


@pytest.mark.parametrize("text", ["", "no box here", "[1, 2, 3]", "[5, 5, 5, 9]", "[1, 2, 3, 4, 5]x"[:0]])
def test_no_box(text):
    assert parse_bbox(text) is None


@pytest.mark.parametrize("w,h", [(640, 480), (1280, 720), (64, 48), (20, 2000)])
def test_fit_size_multiple_of_patch_and_aspect(w, h):
    fw, fh = fit_size(w, h, 896)
    assert fw % _PATCH == 0 and fh % _PATCH == 0 and fw >= _PATCH and fh >= _PATCH
    if min(w, h) / max(w, h) > 0.2:
        assert abs(fw / fh - w / h) < 0.1 * (w / h)
    assert max(fw, fh) <= 896 + _PATCH


def test_fit_size_enlarges_small_frames():
    fw, fh = fit_size(320, 240, 896)
    assert fw > 320 and fh > 240
