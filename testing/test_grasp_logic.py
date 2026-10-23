"""Offline unit tests (no sim): gripper profiles, grasp checks, yaw pose, image bridge, scoring.

    source install/setup.bash && python3 -m pytest testing/test_grasp_logic.py -q
"""
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ur_llm_planner import motion_executor as me  # noqa: E402
from ur_perception.image_convert import NumpyBridge  # noqa: E402
import benchmark_grippers as bench  # noqa: E402


def make_executor(gripper="robotiq_2f_85"):
    """A MotionExecutor without ROS: only the attributes the pure methods read."""
    ex = object.__new__(me.MotionExecutor)
    ex._prefix = ""
    ex._logger = SimpleNamespace(info=lambda *a, **k: None, warn=lambda *a, **k: None,
                                 error=lambda *a, **k: None)
    prof = me.GRIPPER_PROFILES[gripper]
    ex._gripper_joint_name = prof["joint"]
    ex._gripper_closed = prof["closed"]
    ex._tcp_offset_z = prof["tcp_z"]
    ex._latest_joint_state = None
    return ex


def joint_state(name, pos):
    return SimpleNamespace(name=[name], position=[pos])


@pytest.mark.parametrize("gripper", list(me.GRIPPER_PROFILES))
def test_profiles_are_complete(gripper):
    prof = me.GRIPPER_PROFILES[gripper]
    assert prof["closed"] > prof["half"] > 0
    assert 0.1 < prof["tcp_z"] < 0.25


def test_fully_closed_detects_missed_grasp():
    ex = make_executor("robotiq_2f_85")
    assert ex._gripper_fully_closed() is False                      # no joint state: never block a pick
    ex._latest_joint_state = joint_state("finger_joint", 0.79)
    assert ex._gripper_fully_closed() is True                        # all the way shut: nothing held
    ex._latest_joint_state = joint_state("finger_joint", 0.33)
    assert ex._gripper_fully_closed() is False                       # stopped on a 5 cm object


def test_fully_closed_uses_each_grippers_own_limit():
    ex = make_executor("onrobot_rg2")
    ex._latest_joint_state = joint_state("gripper_joint", 1.28)
    assert ex._gripper_fully_closed() is True
    ex._latest_joint_state = joint_state("gripper_joint", 0.7)
    assert ex._gripper_fully_closed() is False


@pytest.mark.parametrize("yaw", [0.0, 0.3, -0.5, math.pi / 4])
def test_downward_pose_points_down_and_turns_by_yaw(yaw):
    pose = make_executor()._make_downward_pose(0.35, 0.0, 0.1, yaw).pose
    q = np.array([pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w])
    assert abs(np.linalg.norm(q) - 1.0) < 1e-9
    x, y, z, w = q
    rot = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                    [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                    [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    assert rot[:, 2] == pytest.approx([0, 0, -1], abs=1e-9)          # tool z points down
    assert math.atan2(rot[1, 0], rot[0, 0]) == pytest.approx(yaw, abs=1e-9)  # tool x turned by yaw


def test_move_above_falls_back_to_lower_hover():
    ex = make_executor()
    tried = []

    def move_to_pose(pose):
        tried.append(pose.pose.position.z)
        return len(tried) == 3                                       # only the third (lowest) hover works

    ex.move_to_pose = move_to_pose
    pose = ex._move_above(0.35, 0.2, 0.1)
    assert pose is not None and len(tried) == 3
    assert tried[0] > tried[1] > tried[2]
    ex.move_to_pose = lambda p: False
    assert ex._move_above(0.35, 0.2, 0.1) is None


def test_numpy_bridge_round_trips():
    b = NumpyBridge()
    img = (np.random.rand(7, 5, 3) * 255).astype(np.uint8)
    msg = b.cv2_to_imgmsg(img, "bgr8")
    assert (b.imgmsg_to_cv2(msg, "bgr8") == img).all()
    assert (b.imgmsg_to_cv2(msg, "rgb8") == img[:, :, ::-1]).all()
    depth = np.random.rand(6, 4).astype(np.float32)
    assert (b.imgmsg_to_cv2(b.cv2_to_imgmsg(depth, "32FC1")) == depth).all()


def test_optical_frame_name():
    from ur_perception.object_detector_node import ObjectDetectorNode
    f = ObjectDetectorNode._optical_frame
    assert f("camera_wrist_depth_frame") == "camera_wrist_depth_optical_frame"
    assert f("camera_head_color_optical_frame") == "camera_head_color_optical_frame"


def test_pick_is_strict_when_height_is_tracked():
    dragged = dict(notes="", lifted_m=0.004)
    lifted = dict(notes="", lifted_m=0.06)
    untracked_moved = dict(notes="", lifted_m=float("nan"))
    untracked_still = dict(notes="object not moved", lifted_m=float("nan"))
    assert not bench._picked(dragged)
    assert bench._picked(lifted)
    assert bench._picked(untracked_moved)
    assert not bench._picked(untracked_still)


def test_carry_speed_lasts_from_pick_to_place_only():
    ex = make_executor()
    ex._speed_scale = me.SPEED_SCALE
    results = {"pick": True, "place": True}

    def impl(task):
        if task["action"] == "pick":
            ex._speed_scale = me.CARRY_SPEED_SCALE      # what _execute_pick does once it holds the object
        return results[task["action"]]

    ex._dispatch_task_impl = impl
    assert ex._dispatch_task({"action": "pick"})
    assert ex._speed_scale == me.CARRY_SPEED_SCALE      # still slow for the place
    assert ex._dispatch_task({"action": "place"})
    assert ex._speed_scale == me.SPEED_SCALE            # back to normal afterwards
    results["pick"] = False
    ex._dispatch_task({"action": "pick"})
    assert ex._speed_scale == me.SPEED_SCALE            # a failed pick never leaves it slow


def test_shape_label_is_voted_across_frames():
    from ur_perception.object_detector_node import ObjectDetectorNode
    node = object.__new__(ObjectDetectorNode)
    pose = SimpleNamespace(pose=SimpleNamespace(position=SimpleNamespace(x=0.35, y=0.0)))
    seen = [node._stable_shape("red", pose, s) for s in ["box", "box", "cylinder", "box", "cylinder", "box"]]
    assert seen[-1] == "box"                                   # one odd frame does not flip the label
    other = SimpleNamespace(pose=SimpleNamespace(position=SimpleNamespace(x=0.35, y=0.30)))
    assert node._stable_shape("red", other, "cylinder") == "cylinder"   # a different spot has its own votes
