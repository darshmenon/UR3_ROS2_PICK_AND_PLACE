#!/usr/bin/env python3
"""
Behavior tree leaf nodes for UR3 pick-and-place.

Each leaf wraps one MotionExecutor call.  Leaves return:
  SUCCESS  — action completed
  FAILURE  — action failed (enables Selector fallback/retry)
  RUNNING  — not used here (all calls block until done)
"""

import threading

import py_trees
from geometry_msgs.msg import PoseStamped
from std_srvs.srv import Trigger


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


class RunMTCPickPlace(py_trees.behaviour.Behaviour):
    """
    One attempt of the MTC pick-and-place task (ur_mtc_pick_place_demo's
    mtc_node), via its run_pick_place (std_srvs/Trigger) service. Each call
    is a fresh attempt: mtc_node re-reads perception (setupPlanningScene)
    and re-plans (new random seed) before executing — see
    MTCTaskNode::runOnePickPlaceAttempt in mtc_node.cpp.

    Unlike the other leaves here (which drive MotionExecutor's direct
    move_group calls with fixed pick/place XYZ params), this leaf hands the
    whole cycle — real point-cloud object detection, MTC's grasp-candidate
    search, collision-aware planning — to mtc_node. Wrap this leaf in a
    py_trees.decorators.Retry to get repeated attempts (see
    build_mtc_retry_tree below): observed failures are RRTConnect
    random-seed variance (~25% raw success rate, 2026-08-08), not a
    deterministic bug, so a fresh attempt is the right recovery.
    """

    def __init__(self, node, service_name: str = "run_pick_place", call_timeout: float = 180.0):
        super().__init__("run_mtc_pick_place")
        self._node = node
        self._client = node.create_client(Trigger, service_name)
        self._call_timeout = call_timeout

    def update(self):
        if not self._client.wait_for_service(timeout_sec=10.0):
            self._node.get_logger().error(
                f"RunMTCPickPlace: service '{self._client.srv_name}' not available"
            )
            return py_trees.common.Status.FAILURE

        future = self._client.call_async(Trigger.Request())
        event = threading.Event()
        future.add_done_callback(lambda _: event.set())
        if not event.wait(timeout=self._call_timeout):
            self._node.get_logger().error("RunMTCPickPlace: service call timed out")
            return py_trees.common.Status.FAILURE

        response = future.result()
        if response is None or not response.success:
            message = response.message if response is not None else "no response"
            self._node.get_logger().warn(f"RunMTCPickPlace: attempt failed — {message}")
            return py_trees.common.Status.FAILURE

        self._node.get_logger().info(f"RunMTCPickPlace: {response.message}")
        return py_trees.common.Status.SUCCESS


def build_mtc_retry_tree(node, max_attempts: int = 5, service_name: str = "run_pick_place"):
    """
    Minimal tree: retry the whole MTC pick-and-place task up to max_attempts
    times, stopping at the first success. See RunMTCPickPlace's docstring
    for why a fresh full-task retry (not a partial/stage-level retry) is the
    right granularity for this failure mode.
    """
    leaf = RunMTCPickPlace(node, service_name=service_name)
    return py_trees.decorators.Retry("mtc_pick_place_with_retry", child=leaf, num_failures=max_attempts)
