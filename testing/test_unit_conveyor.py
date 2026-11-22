"""Pure-logic unit tests for ur_conveyor (no ROS graph needed)."""
import os
import sys
import xml.etree.ElementTree as ET

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ur_conveyor"))
pytest.importorskip("rclpy")
cn = pytest.importorskip("ur_conveyor.conveyor_node")


def _parse(color="red"):
    return ET.fromstring(cn._make_box_sdf("box_1", 0.1, -0.2, 0.3, color))


def test_sdf_is_valid_xml_with_name_and_pose():
    root = _parse()
    assert root.tag == "sdf"
    model = root.find("model")
    assert model.get("name") == "box_1"
    assert [float(v) for v in model.find("pose").text.split()] == [0.1, -0.2, 0.3, 0, 0, 0]


@pytest.mark.parametrize("color", list(cn.COLORS))
def test_sdf_uses_color_rgb(color):
    diffuse = _parse(color).find(".//visual/material/diffuse").text.split()
    assert [float(v) for v in diffuse[:3]] == list(cn.COLORS[color])
    assert diffuse[3] == "1"


def test_sdf_unknown_color_falls_back_to_grey():
    diffuse = _parse("magenta").find(".//visual/material/diffuse").text.split()
    assert [float(v) for v in diffuse[:3]] == [0.5, 0.5, 0.5]


def test_sdf_box_geometry_matches_box_half():
    size = _parse().find(".//collision/geometry/box/size").text.split()
    assert all(float(s) / 2 == pytest.approx(cn.BOX_HALF) for s in size)


def test_colors_are_valid_rgb():
    assert all(len(v) == 3 and all(0 <= c <= 1 for c in v) for v in cn.COLORS.values())
