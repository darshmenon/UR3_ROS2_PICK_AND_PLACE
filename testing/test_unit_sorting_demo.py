"""Pure-logic unit tests for ur_sorting_demo (no ROS graph needed)."""
import glob
import os
import sys
from types import SimpleNamespace

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "ur_sorting_demo"))
for p in glob.glob(os.path.join(ROOT, "install", "ur_interfaces", "local", "lib", "python3*", "dist-packages")):
    sys.path.append(p)

pytest.importorskip("rclpy")
pytest.importorskip("ur_interfaces.msg")
sn = pytest.importorskip("ur_sorting_demo.sorting_node")


def _node(**kw):
    n = sn.SortingNode.__new__(sn.SortingNode)  # skip Node.__init__
    n._enable_split = kw.get("enable", False)
    n._split_axis = kw.get("axis", "y")
    n._split_value = kw.get("value", 0.0)
    n._split_keep_positive = kw.get("positive", True)
    return n


def _obj(x=0.0, y=0.0, label="", oid=""):
    return SimpleNamespace(position=SimpleNamespace(x=x, y=y), label=label, id=oid)


def test_default_bins_shape():
    assert set(sn.DEFAULT_BINS) == {"red", "green", "blue", "yellow", "orange"}
    assert all(len(v) == 3 for v in sn.DEFAULT_BINS.values())
    assert len(set(sn.DEFAULT_BINS.values())) == len(sn.DEFAULT_BINS)


@pytest.mark.parametrize("label,oid,expected", [
    ("red_box", "", "red"), ("", "green_0", "green"), ("BLUE cube", "x", "blue"),
    ("thing", "yellow_3", "yellow"), ("orange", "", "orange"), ("purple", "p_1", ""),
])
def test_color_of(label, oid, expected):
    assert sn.SortingNode._color_of(_obj(label=label, oid=oid)) == expected


def test_split_disabled_accepts_everything():
    n = _node(enable=False)
    assert n._on_my_side(_obj(y=-5)) and n._on_my_side(_obj(y=5))


def test_split_y_positive_and_negative():
    left = _node(enable=True, positive=True)
    right = _node(enable=True, positive=False)
    o_pos, o_neg = _obj(y=0.2), _obj(y=-0.2)
    assert left._on_my_side(o_pos) and not left._on_my_side(o_neg)
    assert right._on_my_side(o_neg) and not right._on_my_side(o_pos)


def test_split_boundary_belongs_to_positive_side():
    assert _node(enable=True, positive=True)._on_my_side(_obj(y=0.0))
    assert not _node(enable=True, positive=False)._on_my_side(_obj(y=0.0))


def test_split_x_axis_and_value():
    n = _node(enable=True, axis="x", value=0.3, positive=True)
    assert n._on_my_side(_obj(x=0.4, y=-9)) and not n._on_my_side(_obj(x=0.2, y=9))
