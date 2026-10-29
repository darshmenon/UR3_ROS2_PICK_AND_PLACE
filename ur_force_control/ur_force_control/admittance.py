"""Cartesian admittance law and a spiral search path, for compliant insertion (peg in hole).

Pure numpy, no ROS. Not validated on the sim yet: only the numerical behaviour is unit-tested
(testing/test_admittance.py).

Admittance: the tool behaves like a mass-spring-damper driven by the measured wrench,

    M * a + D * v + K * (x - x_ref) = F_ext

so a contact force makes the target move away from the surface instead of fighting it. Advance one step with
`Admittance.step(force, x_ref, dt)` and send `pos` as the next Cartesian target.
"""
import math
from dataclasses import dataclass, field
from typing import Iterator, Tuple

import numpy as np


@dataclass
class Admittance:
    mass: np.ndarray = field(default_factory=lambda: np.full(3, 2.0))        # kg (virtual)
    damping: np.ndarray = field(default_factory=lambda: np.full(3, 60.0))    # N s/m
    stiffness: np.ndarray = field(default_factory=lambda: np.full(3, 0.0))   # N/m (0 = pure admittance)
    max_speed: float = 0.05                                                  # m/s clamp
    pos: np.ndarray = field(default_factory=lambda: np.zeros(3))
    vel: np.ndarray = field(default_factory=lambda: np.zeros(3))

    def reset(self, pos):
        self.pos = np.asarray(pos, dtype=float).copy()
        self.vel = np.zeros(3)

    def step(self, force, x_ref, dt: float) -> np.ndarray:
        """One semi-implicit Euler step; returns the new compliant position."""
        force = np.asarray(force, dtype=float)
        acc = (force - self.damping * self.vel - self.stiffness * (self.pos - np.asarray(x_ref, dtype=float))) / self.mass
        self.vel = self.vel + acc * dt
        speed = float(np.linalg.norm(self.vel))
        if speed > self.max_speed:
            self.vel *= self.max_speed / speed
        self.pos = self.pos + self.vel * dt
        return self.pos.copy()


def spiral(pitch: float = 0.0015, max_radius: float = 0.008, step: float = 0.0005) -> Iterator[Tuple[float, float]]:
    """Archimedean spiral offsets (x, y) from the nominal hole position, about `step` metres apart, `pitch` metres
    between turns, until `max_radius`. Use it to search for a hole when the peg tip rests on the surface."""
    theta = 0.0
    while True:
        r = pitch * theta / (2 * math.pi)
        if r > max_radius:
            return
        yield (r * math.cos(theta), r * math.sin(theta))
        theta += step / max(r, step)           # constant arc length between points


def hole_found(force_z: float, depth: float, f_thresh: float = 2.0, d_thresh: float = 0.003) -> bool:
    """The peg has dropped into the hole when the contact force vanishes while the tip is already `d_thresh` deeper
    than the surface."""
    return abs(force_z) < f_thresh and depth > d_thresh
