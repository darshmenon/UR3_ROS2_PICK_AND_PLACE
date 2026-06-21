#!/usr/bin/env python3
"""
Behavior tree leaf nodes for UR3 pick-and-place.

Each leaf wraps one MotionExecutor call.  Leaves return:
  SUCCESS  — action completed
  FAILURE  — action failed (enables Selector fallback/retry)
  RUNNING  — not used here (all calls block until done)
"""

import py_trees
from geometry_msgs.msg import PoseStamped


class MoveToNamedPose(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, executor, group: str, pose_name: str):
        super().__init__(name)
        self._executor = executor
        self._group = group
        self._pose_name = pose_name

    def update(self):
        ok = self._executor.move_to_named_pose(self._group, self._pose_name)
        return (
            py_trees.common.Status.SUCCESS
            if ok
            else py_trees.common.Status.FAILURE
        )


class MoveToPose(py_trees.behaviour.Behaviour):
    def __init__(self, name: str, executor, pose: PoseStamped, group: str = "arm"):
        super().__init__(name)
        self._executor = executor
        self._pose = pose
        self._group = group

    def update(self):
        ok = self._executor.move_to_pose(self._pose, group=self._group)
        return (
            py_trees.common.Status.SUCCESS
            if ok
            else py_trees.common.Status.FAILURE
        )


class OpenGripper(py_trees.behaviour.Behaviour):
    def __init__(self, executor):
        super().__init__("open_gripper")
        self._executor = executor

    def update(self):
        self._executor.open_gripper()
        return py_trees.common.Status.SUCCESS


class CloseGripper(py_trees.behaviour.Behaviour):
    def __init__(self, executor, compliant: bool = False, max_effort: float = 5.0):
        super().__init__("close_gripper" + ("_compliant" if compliant else ""))
        self._executor = executor
        self._compliant = compliant
        self._max_effort = max_effort

    def update(self):
        if self._compliant:
            ok = self._executor.compliant_close_gripper(max_effort=self._max_effort)
        else:
            ok = self._executor.close_gripper()
        return (
            py_trees.common.Status.SUCCESS
            if ok
            else py_trees.common.Status.FAILURE
        )


class Pick(py_trees.behaviour.Behaviour):
    """Full pick sequence: hover → open → descend → compliant_close → lift."""

    def __init__(
        self,
        executor,
        obj_id: str,
        x: float,
        y: float,
        z: float,
        compliant: bool = True,
    ):
        super().__init__(f"pick_{obj_id}")
        self._executor = executor
        self._task = {
            "action": "pick",
            "object_id": obj_id,
            "object_x": x,
            "object_y": y,
            "object_z": z,
        }
        self._compliant = compliant

    def update(self):
        if self._compliant:
            ok = self._executor.compliant_pick(self._task)
        else:
            ok = self._executor.execute_task_list([self._task])
        return (
            py_trees.common.Status.SUCCESS
            if ok
            else py_trees.common.Status.FAILURE
        )


class Place(py_trees.behaviour.Behaviour):
    """Full place sequence: hover → descend → open → retreat."""

    def __init__(self, executor, x: float, y: float, z: float):
        super().__init__(f"place_({x:.2f},{y:.2f})")
        self._executor = executor
        self._task = {"action": "place", "x": x, "y": y, "z": z}

    def update(self):
        ok = self._executor.execute_task_list([self._task])
        return (
            py_trees.common.Status.SUCCESS
            if ok
            else py_trees.common.Status.FAILURE
        )


def build_pick_place_tree(executor, pick_pose: dict, place_pose: dict):
    """
    Build a standard pick-and-place BT.

    Tree structure:
      Sequence [pick_place]
        ├─ home
        ├─ Sequence [pick]
        │    ├─ open_gripper
        │    ├─ pick(x,y,z)          ← with compliant close
        └─ Sequence [place]
             ├─ place(x,y,z)
             └─ home

    A Selector wraps the pick with a retry so a single IK failure retries once.
    """
    root = py_trees.composites.Sequence("pick_place", memory=True)

    root.add_child(MoveToNamedPose("go_home", executor, "arm", "home"))

    pick_seq = py_trees.composites.Sequence("pick", memory=True)
    pick_seq.add_child(OpenGripper(executor))
    pick_seq.add_child(
        Pick(
            executor,
            obj_id=pick_pose.get("id", "obj"),
            x=pick_pose["x"],
            y=pick_pose["y"],
            z=pick_pose["z"],
            compliant=True,
        )
    )

    pick_with_retry = py_trees.composites.Selector("pick_or_retry", memory=False)
    pick_with_retry.add_child(pick_seq)
    pick_with_retry.add_child(
        Pick(
            executor,
            obj_id=pick_pose.get("id", "obj_retry"),
            x=pick_pose["x"],
            y=pick_pose["y"],
            z=pick_pose["z"],
            compliant=False,
        )
    )

    place_seq = py_trees.composites.Sequence("place", memory=True)
    place_seq.add_child(
        Place(executor, place_pose["x"], place_pose["y"], place_pose["z"])
    )
    place_seq.add_child(MoveToNamedPose("return_home", executor, "arm", "home"))

    root.add_child(pick_with_retry)
    root.add_child(place_seq)

    return root
