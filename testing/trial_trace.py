"""Per-trial trace for benchmark_mtc.py (--trace-dir): one .npz for every trial, failed ones included.

Contents, each with the wall time it was received:
  js_*     /joint_states positions and velocities, with their sim-time stamp
  clock_*  /clock, thinned to about 20 Hz (sim seconds against wall seconds gives the real-time factor)
  ctl_*    /arm_controller/controller_state: planned point at that instant (reference), measured point, error
  plan_*   every MTC solution on /solution: each waypoint of each sub-trajectory (before mtc_node repairs
           degenerate sub-trajectories; recovery moves are not published there, but ctl_* covers them)
  meta     JSON string with the trial result
"""
import json
import threading
import time
from pathlib import Path

import numpy as np

CLOCK_PERIOD = 0.05


def _sec(t):
    return t.sec + t.nanosec * 1e-9


def _table(rows, names, key):
    """(len(rows), len(names)) array of rows[i][key], a {joint: value} dict; missing values are NaN."""
    return np.array([[r[key].get(n, np.nan) for n in names] for r in rows], dtype=float).reshape(len(rows), len(names))


def _names(rows, key):
    return sorted({n for r in rows for n in r[key]})


class TrialTrace:
    def __init__(self, out_dir, clock=time.time, parse_clock=None):
        self.out = Path(out_dir)
        self.out.mkdir(parents=True, exist_ok=True)
        self._now = clock
        self._parse_clock = parse_clock
        self._lock = threading.Lock()
        self._name = None
        self._reset()

    def attach(self, node):
        from control_msgs.msg import JointTrajectoryControllerState
        from moveit_task_constructor_msgs.msg import Solution
        from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
        from rclpy.serialization import deserialize_message
        from rosgraph_msgs.msg import Clock
        from sensor_msgs.msg import JointState

        self._parse_clock = lambda raw: deserialize_message(raw, Clock)
        node.create_subscription(JointState, "/joint_states", self.on_joint_state, qos_profile_sensor_data)
        # raw: /clock is fast, so only the samples that are kept get deserialized
        node.create_subscription(Clock, "/clock", self.on_clock, qos_profile_sensor_data, raw=True)
        node.create_subscription(JointTrajectoryControllerState, "/arm_controller/controller_state",
                                 self.on_controller_state, qos_profile_sensor_data)
        latched = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE,
                             durability=DurabilityPolicy.TRANSIENT_LOCAL)
        node.create_subscription(Solution, "/solution", self.on_solution, latched)

    def _reset(self):
        self.js, self.clock, self.ctl, self.plan = [], [], [], []
        self.solutions = 0
        self._last_clock = float("-inf")

    def on_joint_state(self, m):
        with self._lock:
            if self._name is None:
                return
            self.js.append(dict(wall=self._now(), sim=_sec(m.header.stamp), q=dict(zip(m.name, m.position)),
                                qd=dict(zip(m.name, m.velocity))))

    def on_clock(self, m):
        with self._lock:
            wall = self._now()
            if self._name is None or wall - self._last_clock < CLOCK_PERIOD:
                return
            self._last_clock = wall
            if self._parse_clock is not None:
                m = self._parse_clock(m)
            self.clock.append((wall, _sec(m.clock)))

    def on_controller_state(self, m):
        with self._lock:
            if self._name is None:
                return
            n = m.joint_names
            self.ctl.append(dict(wall=self._now(), sim=_sec(m.header.stamp),
                                 ref=dict(zip(n, m.reference.positions)), fb=dict(zip(n, m.feedback.positions)),
                                 err=dict(zip(n, m.error.positions))))

    def on_solution(self, m):
        with self._lock:
            if self._name is None:
                return
            wall = self._now()
            for sub, s in enumerate(m.sub_trajectory):
                jt = s.trajectory.joint_trajectory
                for p in jt.points:
                    self.plan.append(dict(wall=wall, solution=self.solutions, sub=sub, t=_sec(p.time_from_start),
                                          q=dict(zip(jt.joint_names, p.positions))))
            self.solutions += 1

    def start(self, name):
        """Begin a trial. A trial still open (skipped, or the sim hung) is saved first."""
        self.save(note="trial ended without a result")
        with self._lock:
            self._reset()
            self._name = name

    def save(self, **meta):
        """Write the open trial and close it; returns the file path, or None if no trial is open."""
        with self._lock:
            if self._name is None:
                return None
            name, self._name = self._name, None
            js, clk, ctl, plan = self.js, self.clock, self.ctl, self.plan
        data = {"meta": np.array(json.dumps(dict(meta, trial_name=name, solutions=self.solutions)))}
        for prefix, rows, scalars, tables in (("js", js, ("wall", "sim"), ("q", "qd")),
                                              ("ctl", ctl, ("wall", "sim"), ("ref", "fb", "err")),
                                              ("plan", plan, ("wall", "solution", "sub", "t"), ("q",))):
            names = sorted({n for key in tables for n in _names(rows, key)})
            data[f"{prefix}_joints"] = np.array(names, dtype=str)
            for key in scalars:
                data[f"{prefix}_{key}"] = np.array([r[key] for r in rows], dtype=float)
            for key in tables:
                data[f"{prefix}_{key}"] = _table(rows, names, key)
        data["clock_wall"] = np.array([w for w, _ in clk], dtype=float)
        data["clock_sim"] = np.array([s for _, s in clk], dtype=float)
        path = self.out / f"{name}_{int(self._now())}.npz"
        np.savez_compressed(path, **data)
        return path
