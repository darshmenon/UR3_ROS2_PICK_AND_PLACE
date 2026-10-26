"""Offline checks for the conveyor pick-and-sort setup (no simulator needed).

Each one guards a mistake that cost several sim runs: a box colour with no bin (the box is never picked and gets despawned),
a bin outside the UR3's reach with the gripper pointing down, demo bin positions that drifted from the world file, and the
conveyor launch leaving the arm floating (the world has no mount table, so table_height must be 0).
"""
import ast
import math
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WORLD = REPO / "ur_gazebo" / "worlds" / "conveyor_sorting.world"
REACH = 0.46     # m from the arm base, tool pointing down (blue bin at 0.44 m worked, red at 0.29 m and a 0.58 m blue one did not)


def world_bins():
    text = WORLD.read_text()
    bins = {}
    for m in re.finditer(r'<model name="bin_(\w+)">\s*<static>true</static>\s*<pose>([-\d.]+) ([-\d.]+) ', text):
        bins[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return bins


def conveyor_colors():
    tree = ast.parse((REPO / "ur_conveyor" / "ur_conveyor" / "conveyor_node.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "COLORS" for t in node.targets):
            return [k.value for k in node.value.keys]
    raise AssertionError("COLORS not found in conveyor_node.py")


def demo_bins():
    tree = ast.parse((REPO / "testing" / "conveyor_pick_demo.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "BINS" for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError("BINS not found in conveyor_pick_demo.py")


def test_world_has_the_three_bins():
    assert set(world_bins()) == {"red", "green", "blue"}


def test_every_box_colour_has_a_bin():
    missing = [c for c in conveyor_colors() if c not in world_bins()]
    assert not missing, f"boxes of these colours can never be sorted: {missing}"


def test_bins_are_within_reach():
    for color, (x, y) in world_bins().items():
        assert math.hypot(x, y) <= REACH, f"{color} bin at ({x}, {y}) is {math.hypot(x, y):.2f} m from the arm base"


def test_demo_bins_match_world():
    assert demo_bins() == world_bins()


def test_conveyor_launch_puts_arm_on_the_ground():
    text = (REPO / "ur_conveyor" / "launch" / "conveyor.launch.py").read_text()
    assert '"table_height": "0.0"' in text
