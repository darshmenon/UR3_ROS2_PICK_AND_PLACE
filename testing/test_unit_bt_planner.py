"""Pure-logic unit tests for ur_bt_planner leaves/trees with a fake executor."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ur_bt_planner"))
py_trees = pytest.importorskip("py_trees")
pytest.importorskip("rclpy")
pytest.importorskip("geometry_msgs.msg")
pytest.importorskip("std_srvs.srv")
bl = pytest.importorskip("ur_bt_planner.bt_leaves")
S = py_trees.common.Status


class FakeExec:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = []

    def move_to_named_pose(self, group, name):
        self.calls.append(("named", group, name)); return self.ok

    def open_gripper(self):
        self.calls.append(("open",))

    def close_gripper(self):
        self.calls.append(("close",)); return self.ok

    def compliant_close_gripper(self, max_effort):
        self.calls.append(("ccl", max_effort)); return self.ok

    def compliant_pick(self, task):
        self.calls.append(("cpick", task)); return self.ok

    def execute_task_list(self, tasks):
        self.calls.append(("tasks", tasks)); return self.ok


def test_named_pose_status_follows_executor():
    assert bl.MoveToNamedPose("n", FakeExec(True), "arm", "home").update() == S.SUCCESS
    assert bl.MoveToNamedPose("n", FakeExec(False), "arm", "home").update() == S.FAILURE


def test_open_gripper_always_success():
    ex = FakeExec(False)
    assert bl.OpenGripper(ex).update() == S.SUCCESS and ex.calls == [("open",)]


def test_close_gripper_modes():
    ex = FakeExec(True)
    assert bl.CloseGripper(ex).update() == S.SUCCESS
    leaf = bl.CloseGripper(ex, compliant=True, max_effort=7.0)
    assert leaf.name == "close_gripper_compliant"
    assert leaf.update() == S.SUCCESS and ex.calls[-1] == ("ccl", 7.0)
    assert bl.CloseGripper(FakeExec(False)).update() == S.FAILURE


def test_pick_task_and_dispatch():
    ex = FakeExec()
    leaf = bl.Pick(ex, "cube", 0.1, 0.2, 0.3, compliant=True)
    assert leaf.name == "pick_cube"
    assert leaf.update() == S.SUCCESS
    assert ex.calls[0] == ("cpick", {"action": "pick", "object_id": "cube",
                                     "object_x": 0.1, "object_y": 0.2, "object_z": 0.3})
    ex2 = FakeExec(False)
    assert bl.Pick(ex2, "c", 0, 0, 0, compliant=False).update() == S.FAILURE
    assert ex2.calls[0][0] == "tasks"


def test_place_task_and_name():
    ex = FakeExec()
    leaf = bl.Place(ex, 0.25, -0.15, 0.08)
    assert leaf.name == "place_(0.25,-0.15)"
    assert leaf.update() == S.SUCCESS
    assert ex.calls[0][1] == [{"action": "place", "x": 0.25, "y": -0.15, "z": 0.08}]


def _tick(tree):
    tree.setup_with_descendants() if hasattr(tree, "setup_with_descendants") else None
    t = py_trees.trees.BehaviourTree(tree)
    t.tick()
    return tree.status


def test_pick_place_tree_success_runs_all_steps():
    ex = FakeExec(True)
    root = bl.build_pick_place_tree(ex, {"id": "b", "x": .1, "y": .2, "z": .3}, {"x": 0, "y": 0, "z": 0})
    assert root.name == "pick_place"
    assert _tick(root) == S.SUCCESS
    kinds = [c[0] for c in ex.calls]
    assert kinds[0] == "named" and kinds.count("named") == 2 and "cpick" in kinds


def test_pick_place_tree_fails_when_executor_fails():
    ex = FakeExec(False)
    root = bl.build_pick_place_tree(ex, {"x": .1, "y": .2, "z": .3}, {"x": 0, "y": 0, "z": 0})
    assert _tick(root) == S.FAILURE
