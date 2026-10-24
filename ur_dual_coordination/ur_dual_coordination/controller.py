"""Whole-body controller for two arms carrying one object (task-priority differential IK).

Joint velocities of all 12 joints are solved together, in strict priority order:

  1. keep the two hands at the relative pose they grasped the object with   (the object does not get squeezed/pulled)
     + keep the arms apart (a velocity-damper row for the closest pair of sampled arm points)
  2. move the object to its target pose                                     (the minimum-norm solution shares the
                                                                             motion between the two arms)
  3. stay near a comfortable posture                                         (in the null space of 1 and 2)

then joint limits are enforced by freezing the joints that would leave their range and re-solving.
"""
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
import pinocchio as pin

from .kinematics import DualArm


@dataclass
class ControllerConfig:
    k_rel: float = 8.0          # gain on the relative-pose error (1/s)
    k_obj: float = 3.0          # gain on the object-pose error (1/s)
    k_post: float = 0.5         # gain pulling toward the posture, null space only
    damping: float = 0.01       # DLS damping (singularity robustness)
    max_joint_speed: float = 1.2   # rad/s
    safe_distance: float = 0.12    # arms try to stay at least this far apart (m)
    k_avoid: float = 6.0           # separation speed per metre of intrusion inside safe_distance (1/s)
    limit_margin: float = 0.05     # rad kept from the joint limits


@dataclass
class State:
    q: np.ndarray
    obj_error: float = 0.0
    rel_error: float = 0.0
    min_distance: float = 0.0
    saturated: List[str] = field(default_factory=list)


def _pinv(J: np.ndarray, damping: float) -> np.ndarray:
    return J.T @ np.linalg.inv(J @ J.T + damping ** 2 * np.eye(J.shape[0]))


class DualArmController:
    def __init__(self, dual: DualArm, config: Optional[ControllerConfig] = None):
        self.d = dual
        self.cfg = config or ControllerConfig()
        self.lMr_des: Optional[pin.SE3] = None     # relative pose of the right hand in the left hand's frame
        self.lMo: Optional[pin.SE3] = None         # object frame in the left hand's frame
        self.q_posture = np.zeros(dual.nv)

    # -- grasp ---------------------------------------------------------------------------------------
    def set_grasp(self, q: np.ndarray, object_in_left: Optional[pin.SE3] = None):
        """Hold the object at the current configuration. The relative pose of the hands is frozen; the object
        frame defaults to the midpoint between the hands (orientation of the left hand)."""
        self.d.update(q)
        oMl, oMr = self.d.placement(self.d.tool["left"]), self.d.placement(self.d.tool["right"])
        self.lMr_des = oMl.inverse() * oMr
        if object_in_left is None:
            mid = 0.5 * self.lMr_des.translation
            object_in_left = pin.SE3(np.eye(3), mid)
        self.lMo = object_in_left
        self.q_posture = q.copy()

    def object_pose(self, q: np.ndarray) -> pin.SE3:
        self.d.update(q)
        return self.d.placement(self.d.tool["left"]) * self.lMo

    # -- one control step ----------------------------------------------------------------------------
    def step(self, q: np.ndarray, obj_target: pin.SE3, obj_twist_ff: Optional[np.ndarray] = None,
             dt: float = 0.02) -> State:
        c, d = self.cfg, self.d
        d.update(q)
        fl, fr = d.tool["left"], d.tool["right"]
        oMl, oMr = d.placement(fl), d.placement(fr)
        lMr = oMl.inverse() * oMr
        JL, JR = d.jacobian_local(q, fl), d.jacobian_local(q, fr)

        # task 1a: relative pose of the hands (twist of the right frame relative to the left one, in the right frame)
        e_rel = pin.log6(self.lMr_des.inverse() * lMr).vector
        J_rel = JR - lMr.inverse().action @ JL
        rows = [J_rel]
        targets = [-c.k_rel * e_rel]

        # task 1b: keep the arms apart. Inside safe_distance, require the closest pair to move apart at a speed
        # proportional to how far inside it is (a velocity-damper style row, in the top-priority task).
        dmin, pair = self._closest_pair(q)
        if dmin < c.safe_distance and pair is not None:
            (fa, pa), (fb, pb) = pair
            n = (pa - pb) / max(np.linalg.norm(pa - pb), 1e-6)        # points from the right arm's point to the left's
            J_d = n @ (d.jacobian_world_linear(q, fa) - d.jacobian_world_linear(q, fb))
            rows.append(J_d[None, :])
            targets.append(np.array([c.k_avoid * (c.safe_distance - dmin)]))
        J1 = np.vstack(rows)
        v1 = np.concatenate(targets)

        # task 2: the object frame follows its target
        oMo = oMl * self.lMo
        e_obj = pin.log6(obj_target.inverse() * oMo).vector
        J_obj = self.lMo.inverse().action @ JL
        v_obj = -c.k_obj * e_obj
        if obj_twist_ff is not None:
            v_obj = v_obj + obj_twist_ff

        free = np.ones(d.nv, dtype=bool)
        dq = np.zeros(d.nv)
        saturated: List[str] = []
        for _ in range(4):
            dq = self._solve(J1[:, free], v1, J_obj[:, free], v_obj, (self.q_posture - q)[free] * c.k_post, free)
            if self._within_limits(q, dq, dt, free, saturated):
                break
        # joint speed limit: scale the whole vector so the motion direction is preserved
        peak = np.max(np.abs(dq))
        if peak > c.max_joint_speed:
            dq *= c.max_joint_speed / peak
        q_next = np.clip(q + dq * dt, d.lower + 1e-3, d.upper - 1e-3)
        return State(q=q_next, obj_error=float(np.linalg.norm(e_obj)), rel_error=float(np.linalg.norm(e_rel)),
                     min_distance=dmin, saturated=saturated)

    # -- internals -----------------------------------------------------------------------------------
    def _solve(self, J1, v1, J2, v2, post, free):
        lam = self.cfg.damping
        P1 = _pinv(J1, lam)
        dq1 = P1 @ v1
        N1 = np.eye(J1.shape[1]) - P1 @ J1
        J2n = J2 @ N1
        dq2 = dq1 + _pinv(J2n, lam) @ (v2 - J2 @ dq1)
        # null space of both tasks for the posture term
        Jall = np.vstack([J1, J2])
        N12 = np.eye(Jall.shape[1]) - _pinv(Jall, lam) @ Jall
        dq = dq2 + N12 @ post
        full = np.zeros(self.d.nv)
        full[free] = dq
        return full

    def _within_limits(self, q, dq, dt, free, saturated) -> bool:
        c = self.cfg
        nxt = q + dq * dt
        lo, hi = self.d.lower + c.limit_margin, self.d.upper - c.limit_margin
        bad = (nxt < lo) | (nxt > hi)
        # only joints moving further out of range are frozen (a joint inside the margin may move back in)
        bad &= ((nxt < lo) & (dq < 0)) | ((nxt > hi) & (dq > 0))
        bad &= free
        if not bad.any():
            return True
        for i in np.where(bad)[0]:
            free[i] = False
            name = next((n for n, col in self.d.col.items() if col == i), str(i))
            if name not in saturated:
                saturated.append(name)
        return False

    def _closest_pair(self, q):
        d = self.d
        best, pair = np.inf, None
        for fa in d.guard["left"]:
            for fb in d.guard["right"]:
                pa, pb = d.data.oMf[fa].translation, d.data.oMf[fb].translation
                dist = float(np.linalg.norm(pa - pb))
                if dist < best:
                    best, pair = dist, ((fa, pa.copy()), (fb, pb.copy()))
        return best, pair


def reach_poses(dual: DualArm, q0: np.ndarray, target_left: pin.SE3, target_right: pin.SE3,
                iterations: int = 400, gain: float = 2.0, damping: float = 0.02, dt: float = 0.05):
    """Drive both tool frames to given world poses (plain damped least squares); returns (q, left_err, right_err).

    Used to find a pose where the hands hold an object between them, before the cooperative controller takes over.
    """
    q = q0.copy()
    for _ in range(iterations):
        dual.update(q)
        fl, fr = dual.tool["left"], dual.tool["right"]
        eL = pin.log6(target_left.inverse() * dual.placement(fl)).vector
        eR = pin.log6(target_right.inverse() * dual.placement(fr)).vector
        J = np.vstack([dual.jacobian_local(q, fl), dual.jacobian_local(q, fr)])
        dq = _pinv(J, damping) @ (-gain * np.concatenate([eL, eR]))
        q = np.clip(q + np.clip(dq, -1.5, 1.5) * dt, dual.lower + 0.02, dual.upper - 0.02)
    dual.update(q)
    eL = pin.log6(target_left.inverse() * dual.placement(dual.tool["left"])).vector
    eR = pin.log6(target_right.inverse() * dual.placement(dual.tool["right"])).vector
    return q, float(np.linalg.norm(eL)), float(np.linalg.norm(eR))
