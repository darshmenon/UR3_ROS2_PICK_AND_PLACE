"""Kinematic model of the two-arm UR3 robot (12 joints) built with Pinocchio.

The gripper joints are locked, so the model is exactly the two arms. Everything the whole-body controller
needs comes from here: frame placements, local-frame Jacobians, joint limits and a few points along each arm
for inter-arm distance checks.
"""
from typing import Dict, List, Sequence

import numpy as np
import pinocchio as pin

ARM_JOINTS = ("shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
              "wrist_1_joint", "wrist_2_joint", "wrist_3_joint")
# Links sampled along each arm for the inter-arm distance check (name suffixes, prefixed with left_/right_).
GUARD_LINKS = ("upper_arm_link", "forearm_link", "wrist_2_link", "wrist_3_link", "tool0")


class DualArm:
    """Pinocchio model of left_*/right_* UR3 arms with the grippers locked."""

    def __init__(self, urdf_xml: str, tool_frame: str = "tool0"):
        full = pin.buildModelFromXML(urdf_xml)
        self.joint_names: List[str] = [f"{side}_{j}" for side in ("left", "right") for j in ARM_JOINTS]
        lock = [jid for jid, name in enumerate(full.names)
                if jid != 0 and name not in self.joint_names]
        self.model = pin.buildReducedModel(full, lock, pin.neutral(full))
        self.data = self.model.createData()
        self.nv = self.model.nv
        # column of each named joint in q / dq
        self.col: Dict[str, int] = {n: self.model.idx_qs[self.model.getJointId(n)] for n in self.joint_names}
        self.left_cols = [self.col[f"left_{j}"] for j in ARM_JOINTS]
        self.right_cols = [self.col[f"right_{j}"] for j in ARM_JOINTS]
        self.tool = {"left": self.model.getFrameId(f"left_{tool_frame}"),
                     "right": self.model.getFrameId(f"right_{tool_frame}")}
        self.guard = {side: [self.model.getFrameId(f"{side}_{l}") for l in GUARD_LINKS] for side in ("left", "right")}
        self.lower = np.array(self.model.lowerPositionLimit)
        self.upper = np.array(self.model.upperPositionLimit)

    # -- helpers -----------------------------------------------------------------------------------
    def q_from_dict(self, positions: Dict[str, float], default: float = 0.0) -> np.ndarray:
        q = np.full(self.nv, default)
        for name, c in self.col.items():
            if name in positions:
                q[c] = positions[name]
        return q

    def update(self, q: np.ndarray):
        pin.forwardKinematics(self.model, self.data, q)
        pin.updateFramePlacements(self.model, self.data)

    def placement(self, frame_id: int) -> pin.SE3:
        return self.data.oMf[frame_id]

    def jacobian_local(self, q: np.ndarray, frame_id: int) -> np.ndarray:
        return pin.computeFrameJacobian(self.model, self.data, q, frame_id, pin.ReferenceFrame.LOCAL)

    def jacobian_world_linear(self, q: np.ndarray, frame_id: int) -> np.ndarray:
        return pin.computeFrameJacobian(self.model, self.data, q, frame_id,
                                        pin.ReferenceFrame.LOCAL_WORLD_ALIGNED)[:3]

    def guard_points(self, side: str) -> List[np.ndarray]:
        return [self.data.oMf[f].translation.copy() for f in self.guard[side]]

    def min_arm_distance(self, q: np.ndarray) -> float:
        """Smallest distance between any sampled point of the left arm and any of the right arm."""
        self.update(q)
        left, right = self.guard_points("left"), self.guard_points("right")
        return min(float(np.linalg.norm(a - b)) for a in left for b in right)
