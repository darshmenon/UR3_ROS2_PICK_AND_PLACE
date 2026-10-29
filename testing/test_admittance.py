"""Offline tests for ur_force_control.admittance (no ROS, no sim)."""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ur_force_control"))
from ur_force_control.admittance import Admittance, hole_found, spiral  # noqa: E402


def run(adm, force, seconds, dt=0.002, x_ref=(0, 0, 0)):
    for _ in range(int(seconds / dt)):
        adm.step(force, x_ref, dt)
    return adm.pos


def test_free_space_force_gives_terminal_velocity():
    a = Admittance()
    a.reset([0, 0, 0])
    run(a, [0, 0, -3.0], 2.0)
    # F = D v at steady state -> v = 3/60 = 0.05 m/s, which is also the speed clamp
    assert abs(a.vel[2] + 0.05) < 2e-3


def test_no_force_stays_put():
    a = Admittance()
    a.reset([0.1, 0.2, 0.3])
    assert np.allclose(run(a, [0, 0, 0], 1.0), [0.1, 0.2, 0.3])


def test_spring_returns_to_reference():
    a = Admittance(stiffness=np.full(3, 200.0))
    a.reset([0.02, 0, 0])
    p = run(a, [0, 0, 0], 4.0)
    assert np.linalg.norm(p) < 1e-3


def test_speed_clamp():
    a = Admittance(max_speed=0.02)
    a.reset([0, 0, 0])
    run(a, [50, 0, 0], 1.0)
    assert np.linalg.norm(a.vel) <= 0.02 + 1e-9


def test_compliance_yields_to_a_wall():
    """Pushing down onto a stiff surface at z=0: a contact force opposes the push, the target settles near the wall."""
    a = Admittance(stiffness=np.full(3, 100.0))
    a.reset([0, 0, 0.01])
    for _ in range(5000):
        contact = max(0.0, -a.pos[2]) * 5000.0         # wall spring
        a.step([0, 0, -5.0 + contact], [0, 0, 0.0], 0.002)
    assert -0.003 < a.pos[2] < 0.001


def test_spiral_is_bounded_and_evenly_spaced():
    pts = np.array(list(spiral(pitch=0.0015, max_radius=0.008, step=0.0005)))
    assert len(pts) > 50
    assert np.max(np.hypot(pts[:, 0], pts[:, 1])) <= 0.008 + 1e-9
    d = np.hypot(*np.diff(pts, axis=0).T)
    assert d[5:].max() < 0.0012                       # no big jumps after the first turn
    # it covers all directions
    assert pts[:, 0].min() < -0.004 and pts[:, 0].max() > 0.004 and pts[:, 1].min() < -0.004 and pts[:, 1].max() > 0.004


def test_hole_found():
    assert hole_found(0.5, 0.005)
    assert not hole_found(8.0, 0.005)
    assert not hole_found(0.5, 0.001)
