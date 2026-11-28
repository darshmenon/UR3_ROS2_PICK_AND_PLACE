"""Offline tests for testing/trial_trace.py (no ROS, no sim)."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from trial_trace import TrialTrace  # noqa: E402


def stamp(t):
    return NS(sec=int(t), nanosec=int(round((t - int(t)) * 1e9)))


class Wall:
    def __init__(self):
        self.t = 100.0

    def __call__(self):
        return self.t


def joint_state(t, q):
    return NS(header=NS(stamp=stamp(t)), name=list(q), position=list(q.values()), velocity=[0.0] * len(q))


def solution(*subs):
    return NS(sub_trajectory=[NS(trajectory=NS(joint_trajectory=NS(
        joint_names=names, points=[NS(time_from_start=stamp(t), positions=p) for t, p in pts])))
        for names, pts in subs])


def feed(trace, wall):
    trace.on_joint_state(joint_state(1.5, {"wrist_1_joint": 0.1, "elbow_joint": 0.2}))
    trace.on_controller_state(NS(header=NS(stamp=stamp(1.5)), joint_names=["wrist_1_joint"],
                                 reference=NS(positions=[2.0]), feedback=NS(positions=[0.1]),
                                 error=NS(positions=[1.9])))
    trace.on_solution(solution((["wrist_1_joint"], [(0.0, [0.0]), (0.5, [2.0])]),
                               (["finger_joint"], [(0.0, [0.4])])))
    for _ in range(100):                  # 100 clock messages 1 ms apart: thinned to about 20 Hz
        wall.t += 0.001
        trace.on_clock(NS(clock=stamp(wall.t - 99.0)))


def load(path):
    with np.load(path) as d:
        return {k: d[k] for k in d.files}


def test_records_failed_trial(tmp_path):
    wall = Wall()
    trace = TrialTrace(tmp_path, clock=wall)
    trace.start("t14")
    feed(trace, wall)
    d = load(trace.save(success=False, notes="stall"))
    meta = json.loads(str(d["meta"]))
    assert meta["success"] is False and meta["trial_name"] == "t14" and meta["solutions"] == 1
    assert list(d["js_joints"]) == ["elbow_joint", "wrist_1_joint"]
    assert np.allclose(d["js_q"], [[0.2, 0.1]]) and np.allclose(d["js_sim"], [1.5])
    assert np.allclose(d["ctl_ref"], [[2.0]]) and np.allclose(d["ctl_err"], [[1.9]])
    assert list(d["plan_sub"]) == [0, 0, 1] and np.allclose(d["plan_t"], [0.0, 0.5, 0.0])
    assert np.isnan(d["plan_q"][2, list(d["plan_joints"]).index("wrist_1_joint")])
    assert 2 <= len(d["clock_sim"]) <= 3 and np.all(np.diff(d["clock_wall"]) >= 0.05 - 1e-9)


def test_ignores_messages_outside_a_trial(tmp_path):
    wall = Wall()
    trace = TrialTrace(tmp_path, clock=wall)
    feed(trace, wall)
    assert trace.save(success=True) is None
    trace.start("a")
    d = load(trace.save(success=True))
    assert d["js_q"].shape == (0, 0) and d["clock_sim"].size == 0 and d["plan_q"].shape == (0, 0)


def test_unsaved_trial_is_kept_when_the_next_starts(tmp_path):
    wall = Wall()
    trace = TrialTrace(tmp_path, clock=wall)
    trace.start("skipped")
    feed(trace, wall)
    trace.start("next")
    (path,) = tmp_path.glob("skipped_*.npz")
    d = load(path)
    assert json.loads(str(d["meta"]))["note"] == "trial ended without a result"
    assert len(d["js_sim"]) == 1
    assert load(trace.save(success=True))["js_sim"].size == 0
    assert trace.save(success=True) is None


def test_clock_parser_runs_only_for_kept_samples(tmp_path):
    wall, seen = Wall(), []
    trace = TrialTrace(tmp_path, clock=wall, parse_clock=lambda raw: seen.append(raw) or NS(clock=stamp(raw)))
    trace.start("c")
    for i in range(10):
        wall.t += 0.01
        trace.on_clock(float(i))
    assert len(seen) == len(load(trace.save())["clock_sim"]) < 10
