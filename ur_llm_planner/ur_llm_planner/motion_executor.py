#!/usr/bin/env python3
"""
Motion executor for the UR3 LLM planner.

Bridges structured task dicts (produced by ClaudeClient) with actual
ROS 2 action clients that command the robot arm and gripper.
"""

import math
import threading

import rclpy.time
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node

from action_msgs.msg import GoalStatus
from control_msgs.action import GripperCommand
from geometry_msgs.msg import PoseStamped
from moveit_msgs.action import MoveGroup as MoveGroupAction
from moveit_msgs.msg import (
    BoundingVolume,
    Constraints,
    JointConstraint,
    MotionPlanRequest,
    MoveItErrorCodes,
    OrientationConstraint,
    PositionConstraint,
    RobotState,
)
from moveit_msgs.srv import GetPositionIK
from sensor_msgs.msg import JointState
from shape_msgs.msg import SolidPrimitive
from tf2_ros import Buffer, TransformListener, LookupException, ExtrapolationException

# Gripper position constants (metres, used by GripperActionController)
GRIPPER_OPEN = 0.0    # fully open
GRIPPER_CLOSED = 0.8  # fully closed (maps ~85 mm stroke)
GRIPPER_HALF = 0.4    # half-closed

# Named arm poses from ur.srdf — used to build explicit JointConstraints because
# MoveIt's action API does NOT resolve Constraints.name as a named state.
_ARM_JOINTS = [
    "shoulder_pan_joint",
    "shoulder_lift_joint",
    "elbow_joint",
    "wrist_1_joint",
    "wrist_2_joint",
    "wrist_3_joint",
]
# UR3 URDF joint limits [lower, upper] in radians
_ARM_JOINT_LIMITS = [
    (-6.2832, 6.2832),   # shoulder_pan_joint  ±2π
    (-6.2832, 6.2832),   # shoulder_lift_joint ±2π
    (-3.1416, 3.1416),   # elbow_joint         ±π  ← narrower!
    (-6.2832, 6.2832),   # wrist_1_joint       ±2π
    (-6.2832, 6.2832),   # wrist_2_joint       ±2π
    (-6.2832, 6.2832),   # wrist_3_joint       ±2π
]
_NAMED_ARM_POSES: dict[str, list[float]] = {
    # [pan, lift, elbow, w1, w2, w3]
    "home":  [0.0, 4.6169, 0.0, 0.0, 0.0, 0.0],
    "ready": [0.0, 4.6169, 0.0, 0.0, 0.0, 1.0],
}
_NAMED_GRIPPER_POSES: dict[str, float] = {
    "open":        0.0,
    "closed":      0.8,
    "half_closed": 0.6,
}
_JOINT_TOLERANCE = 0.01  # radians

# Pre-grasp approach height above the target object (metres)
PREGRASP_HEIGHT_OFFSET = 0.12

# Default place height above table
DEFAULT_PLACE_Z = 0.10

# The "arm" group's IK tip link is tool0 (the flange), but for a downward-
# pointing Robotiq 2F-85 the fingertip contact point sits ~145mm further
# along tool0's +Z (10mm mount + ~135mm through knuckles/pads) — same value
# as ur_visual_servo/servo_node.py's tcp_offset_xyz. move_to_pose() drives
# tool0, so pick/place targets must add this offset or the gripper closes
# ~145mm below the intended contact height.
GRIPPER_TCP_OFFSET_Z = 0.145


class MotionExecutor:
    """
    Executes robot motion commands via ROS 2 action clients.

    Supports:
    - Moving the arm to named poses (via MoveGroup)
    - Moving the arm to Cartesian poses (via MoveGroup)
    - Opening / closing the gripper (via GripperCommand)
    - Executing a sequential list of task dicts produced by OllamaClient
    """

    def __init__(self, node: Node):
        """
        Initialise action clients.

        Args:
            node: An rclpy Node used to create action clients and for logging.
        """
        self._node = node
        self._logger = node.get_logger()

        self._move_group_client = ActionClient(
            node,
            MoveGroupAction,
            "/move_action",
        )

        self._gripper_client = ActionClient(
            node,
            GripperCommand,
            "/gripper_controller/gripper_cmd",
        )

        self._ik_client = node.create_client(GetPositionIK, "/compute_ik")

        self._latest_joint_state: JointState | None = None
        node.create_subscription(
            JointState, "/joint_states", self._joint_state_cb, 10
        )

        # For move_relative — need the actual current end-effector pose to
        # offset from, not just joint values (see get_current_pose below).
        self._tf_buffer = Buffer()
        self._tf_listener = TransformListener(self._tf_buffer, node)

    def _joint_state_cb(self, msg: JointState) -> None:
        self._latest_joint_state = msg

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def wait_for_servers(self, timeout: float = 5.0) -> bool:
        """
        Wait for action servers to become available.

        Args:
            timeout: Seconds to wait for each server.

        Returns:
            True if both servers are available, False otherwise.
        """
        self._logger.info("Waiting for /move_action server...")
        move_ok = self._move_group_client.wait_for_server(timeout_sec=timeout)
        if not move_ok:
            self._logger.warn(
                f"/move_action server not available after {timeout}s — "
                "motion commands will be skipped."
            )

        self._logger.info("Waiting for /gripper_controller/gripper_cmd server...")
        gripper_ok = self._gripper_client.wait_for_server(timeout_sec=timeout)
        if not gripper_ok:
            self._logger.warn(
                f"/gripper_controller/gripper_cmd server not available after {timeout}s — "
                "gripper commands will be skipped."
            )

        return move_ok and gripper_ok

    def move_to_named_pose(
        self,
        group_name: str,
        pose_name: str,
        timeout: float = 30.0,
    ) -> bool:
        """
        Move a planning group to a named joint-space pose.

        Args:
            group_name: MoveIt planning group (e.g. "arm", "gripper").
            pose_name:  Named state defined in the SRDF (e.g. "home", "ready").
            timeout:    Action timeout in seconds.

        Returns:
            True on success, False on failure.
        """
        self._logger.info(
            f"[MotionExecutor] move_to_named_pose: group={group_name} pose={pose_name}"
        )

        if not self._move_group_client.server_is_ready():
            self._logger.warn("MoveGroup server not ready — skipping move_to_named_pose.")
            return False

        # Resolve named pose to explicit joint values.
        # MoveIt's action API does NOT look up named states from Constraints.name —
        # that is a C++ MoveGroupInterface convenience. We must supply real JointConstraints.
        if group_name == "arm" or group_name == "arm_with_gripper":
            joint_values = _NAMED_ARM_POSES.get(pose_name)
            if joint_values is None:
                self._logger.error(
                    f"Unknown named arm pose '{pose_name}'. "
                    f"Known: {list(_NAMED_ARM_POSES.keys())}"
                )
                return False
            joint_names = _ARM_JOINTS
        elif group_name == "gripper":
            finger_pos = _NAMED_GRIPPER_POSES.get(pose_name)
            if finger_pos is None:
                self._logger.error(
                    f"Unknown named gripper pose '{pose_name}'. "
                    f"Known: {list(_NAMED_GRIPPER_POSES.keys())}"
                )
                return False
            joint_names = ["finger_joint"]
            joint_values = [finger_pos]
        else:
            self._logger.error(f"Unknown group '{group_name}' for named pose move.")
            return False

        goal = MoveGroupAction.Goal()
        req: MotionPlanRequest = goal.request
        req.group_name = group_name
        req.num_planning_attempts = 5
        req.allowed_planning_time = min(timeout * 0.7, 10.0)
        req.max_velocity_scaling_factor = 0.3
        req.max_acceleration_scaling_factor = 0.3
        # Use Pilz PTP — generates its own timestamps, avoids TOTG zero-duration bug
        req.pipeline_id = "pilz_industrial_motion_planner"
        req.planner_id = "PTP"
        req.allowed_planning_time = min(timeout * 0.9, 15.0)

        constraints = Constraints()
        constraints.name = pose_name  # label only
        for name, value in zip(joint_names, joint_values):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = value
            jc.tolerance_above = _JOINT_TOLERANCE
            jc.tolerance_below = _JOINT_TOLERANCE
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)
        req.goal_constraints.append(constraints)

        return self._send_move_group_goal(goal, timeout)

    def open_gripper(self, timeout: float = 10.0) -> bool:
        """Open the gripper fully."""
        self._logger.info("[MotionExecutor] open_gripper")
        return self._send_gripper_goal(GRIPPER_OPEN, 10.0, timeout)

    def close_gripper(self, timeout: float = 20.0) -> bool:
        """Close the gripper fully."""
        self._logger.info("[MotionExecutor] close_gripper")
        return self._send_gripper_goal(GRIPPER_CLOSED, 10.0, timeout)

    def compliant_close_gripper(
        self, max_effort: float = 5.0, timeout: float = 20.0
    ) -> bool:
        """Close gripper with force limit — stops on contact (stall).

        Uses a low max_effort so the GripperActionController stalls when
        it hits an object rather than driving through it.  The result's
        `stalled` flag tells us whether contact was detected.
        """
        self._logger.info(
            f"[MotionExecutor] compliant_close_gripper (max_effort={max_effort})"
        )
        return self._send_gripper_goal(GRIPPER_CLOSED, max_effort, timeout)

    def half_close_gripper(self, timeout: float = 10.0) -> bool:
        """Close the gripper to half position."""
        self._logger.info("[MotionExecutor] half_close_gripper")
        return self._send_gripper_goal(GRIPPER_HALF, 10.0, timeout)

    def get_current_pose(
        self, tip_frame: str = "tool0", reference_frame: str = "base_link", timeout: float = 2.0
    ) -> PoseStamped | None:
        """
        Look up the live end-effector pose via TF (not joint values — a
        Cartesian offset needs the actual pose, not FK done by hand).

        Returns None if the transform isn't available (e.g. robot_state_publisher
        not up yet); callers should treat that as a hard failure, not silently
        substitute a guessed pose.
        """
        try:
            tf = self._tf_buffer.lookup_transform(
                reference_frame, tip_frame, rclpy.time.Time(),
                timeout=Duration(seconds=timeout),
            )
        except (LookupException, ExtrapolationException) as e:
            self._logger.error(f"[MotionExecutor] get_current_pose: TF lookup failed — {e}")
            return None

        pose = PoseStamped()
        pose.header.frame_id = reference_frame
        pose.pose.position.x = tf.transform.translation.x
        pose.pose.position.y = tf.transform.translation.y
        pose.pose.position.z = tf.transform.translation.z
        pose.pose.orientation = tf.transform.rotation
        return pose

    def move_relative(
        self,
        dx: float = 0.0,
        dy: float = 0.0,
        dz: float = 0.0,
        group: str = "arm",
        timeout: float = 30.0,
    ) -> bool:
        """
        Move the end-effector by (dx, dy, dz) metres in base_link from
        wherever it currently is, keeping its current orientation. This is
        what "move up/down/left/right by N cm" commands need — pick/place
        only support absolute targets, and the LLM has no way to know the
        current pose to compute one itself.

        Values come from an LLM, not a human — the prompt tells it these are
        metres, but a small local model can still mix up units (e.g. write
        the centimetre number directly) or sign. Clamp rather than trust, so
        a bad LLM output can't send the arm on a multi-metre excursion; IK
        would reject an unreachable target anyway, but this fails fast with
        a clear reason instead of a generic "-31" from /compute_ik.
        """
        _MAX_STEP = 0.5  # metres — generous vs. the UR3's ~0.5m reach, well past any real "nudge"
        clamped = {
            "dx": max(-_MAX_STEP, min(_MAX_STEP, dx)),
            "dy": max(-_MAX_STEP, min(_MAX_STEP, dy)),
            "dz": max(-_MAX_STEP, min(_MAX_STEP, dz)),
        }
        if (clamped["dx"], clamped["dy"], clamped["dz"]) != (dx, dy, dz):
            self._logger.warn(
                f"[MotionExecutor] move_relative: requested ({dx}, {dy}, {dz}) exceeds "
                f"±{_MAX_STEP}m sanity limit — clamping to ({clamped['dx']}, {clamped['dy']}, {clamped['dz']}). "
                "This usually means the LLM used the wrong units (e.g. cm instead of m)."
            )
        dx, dy, dz = clamped["dx"], clamped["dy"], clamped["dz"]

        current = self.get_current_pose()
        if current is None:
            self._logger.error("[MotionExecutor] move_relative: could not get current pose — aborting.")
            return False

        target = PoseStamped()
        target.header.frame_id = current.header.frame_id
        target.pose.position.x = current.pose.position.x + dx
        target.pose.position.y = current.pose.position.y + dy
        target.pose.position.z = current.pose.position.z + dz
        target.pose.orientation = current.pose.orientation

        self._logger.info(
            f"[MotionExecutor] move_relative: ({dx:+.3f}, {dy:+.3f}, {dz:+.3f}) from "
            f"({current.pose.position.x:.3f}, {current.pose.position.y:.3f}, {current.pose.position.z:.3f}) "
            f"to ({target.pose.position.x:.3f}, {target.pose.position.y:.3f}, {target.pose.position.z:.3f})"
        )
        return self.move_to_pose(target, group=group, timeout=timeout)

    def move_to_pose(
        self,
        pose: PoseStamped,
        group: str = "arm",
        timeout: float = 30.0,
    ) -> bool:
        """
        Plan and execute a Cartesian end-effector pose goal via IK → Pilz PTP.

        Uses /compute_ik to get joint angles, then Pilz PTP for time-stamped
        execution (avoids TOTG zero-duration bug with OMPL in Humble).
        """
        self._logger.info(
            f"[MotionExecutor] move_to_pose: group={group} "
            f"pos=({pose.pose.position.x:.3f}, {pose.pose.position.y:.3f}, "
            f"{pose.pose.position.z:.3f})"
        )

        joint_values = self._compute_ik(pose, group, timeout=5.0)
        if joint_values is None:
            self._logger.error("[MotionExecutor] IK failed — cannot reach target pose.")
            return False

        self._logger.info(
            f"[MotionExecutor] IK solution: {[f'{v:.3f}' for v in joint_values]}"
        )
        # Use Pilz PTP with the IK solution (avoids TOTG)
        return self._move_to_joint_values(group, joint_values, timeout)

    def _compute_ik(self, pose: PoseStamped, group: str, timeout: float = 5.0):
        """Call /compute_ik and return joint values list, or None on failure."""
        if not self._ik_client.wait_for_service(timeout_sec=timeout):
            self._logger.error("/compute_ik service not available.")
            return None

        req = GetPositionIK.Request()
        req.ik_request.group_name = group
        req.ik_request.pose_stamped = pose
        req.ik_request.timeout.sec = int(timeout)
        req.ik_request.avoid_collisions = True
        # Build an IK seed.
        # When the arm is at home (elbow≈0, arm straight up) KDL cannot reliably
        # converge to a natural downward-grasp configuration — it drifts to a
        # wrapped "behind-the-back" solution (shoulder_pan ≈ -π + target) that
        # Pilz PTP then flags as INVALID_MOTION_PLAN because the path sweeps
        # through a colliding region.
        # Fix: use a fixed "natural downward grasp" seed whenever the current
        # elbow is near 0 (home-like), otherwise seed from current state.
        # Natural seed: pan→target, lift≈-2.2, elbow≈2.2, w1≈-1.6, w2≈-π/2, w3≈0
        _NATURAL_GRASP_SEED = [-99.0, -2.2, 2.2, -1.6, -1.571, 0.0]  # pan filled below
        target_pan = math.atan2(
            pose.pose.position.y, pose.pose.position.x
        )
        seed_js = JointState()
        current_elbow = 0.0
        if self._latest_joint_state is not None and \
                "elbow_joint" in self._latest_joint_state.name:
            ei = self._latest_joint_state.name.index("elbow_joint")
            current_elbow = self._latest_joint_state.position[ei]

        if abs(current_elbow) < 0.3:
            # Arm near home — use natural downward-grasp seed
            seed_positions = list(_NATURAL_GRASP_SEED)
            seed_positions[0] = target_pan
            seed_js.name = list(_ARM_JOINTS)
            seed_js.position = seed_positions
        else:
            # Already in a pick-like pose — seed from current state + override pan
            seed_js = JointState(
                name=list(self._latest_joint_state.name),
                position=list(self._latest_joint_state.position),
            )
            if "shoulder_pan_joint" in seed_js.name:
                idx = seed_js.name.index("shoulder_pan_joint")
                seed_js.position[idx] = target_pan
        req.ik_request.robot_state.joint_state = seed_js

        future = self._ik_client.call_async(req)
        if not self._wait_for_future(future, timeout + 1.0):
            self._logger.error("/compute_ik call timed out.")
            return None

        resp = future.result()
        if resp.error_code.val != MoveItErrorCodes.SUCCESS:
            self._logger.error(
                f"/compute_ik failed with error code {resp.error_code.val}"
            )
            return None

        joint_state = resp.solution.joint_state
        group_joints = _ARM_JOINTS if group in ("arm", "arm_with_gripper") else []

        # Get a reference (home or current) so we can canonicalize joint values.
        # KDL can return 2π-equivalent solutions; we pick the one closest to the
        # reference to avoid large sweeping motions that trigger path collisions.
        ref = list(_NAMED_ARM_POSES.get("home", [0.0] * 6))
        if self._latest_joint_state is not None:
            js = self._latest_joint_state
            for i, jname in enumerate(_ARM_JOINTS):
                if jname in js.name:
                    ref[i] = js.position[js.name.index(jname)]

        values = []
        for i, jname in enumerate(group_joints):
            if jname not in joint_state.name:
                self._logger.error(f"Joint {jname} not in IK solution.")
                return None
            raw = joint_state.position[joint_state.name.index(jname)]
            # Normalise to the 2π-branch closest to the reference value,
            # then verify it is within the joint's URDF limits.
            # Pick the 2π-branch of raw closest to ref[i].
            # Use math.floor(x+0.5) for round-half-up (avoids Python banker's rounding
            # at x=0.5 which can leave the value 2π away from the reference).
            diff = raw - ref[i]
            n = math.floor(diff / (2 * math.pi) + 0.5)
            raw -= n * 2 * math.pi
            lo, hi = _ARM_JOINT_LIMITS[i]
            if raw < lo:
                raw += 2 * math.pi
            elif raw > hi:
                raw -= 2 * math.pi
            values.append(raw)
        return values

    def _move_to_joint_values(
        self, group: str, joint_values: list, timeout: float = 30.0
    ) -> bool:
        """Move a group to explicit joint values using Pilz PTP."""
        goal = MoveGroupAction.Goal()
        req: MotionPlanRequest = goal.request
        req.group_name = group
        req.num_planning_attempts = 3
        req.allowed_planning_time = min(timeout * 0.7, 10.0)
        req.max_velocity_scaling_factor = 0.3
        req.max_acceleration_scaling_factor = 0.3
        req.pipeline_id = "pilz_industrial_motion_planner"
        req.planner_id = "PTP"

        constraints = Constraints()
        for name, value in zip(_ARM_JOINTS, joint_values):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = value
            jc.tolerance_above = _JOINT_TOLERANCE
            jc.tolerance_below = _JOINT_TOLERANCE
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)
        req.goal_constraints.append(constraints)
        return self._send_move_group_goal(goal, timeout)

    def execute_task_list(self, tasks: list[dict]) -> bool:
        """
        Execute a sequential list of task dicts.

        Supported actions:
            move_to_named_pose  – {"action": "move_to_named_pose", "pose_name": str}
            pick                – {"action": "pick", "object_id": str,
                                   "object_x": float, "object_y": float, "object_z": float}
            place               – {"action": "place", "x": float, "y": float, "z": float}
            open_gripper        – {"action": "open_gripper"}
            close_gripper       – {"action": "close_gripper"}

        Args:
            tasks: Ordered list of action dicts.

        Returns:
            True if all tasks completed successfully, False if any failed.
        """
        if not tasks:
            self._logger.warn("[MotionExecutor] execute_task_list called with empty list.")
            return True

        self._logger.info(
            f"[MotionExecutor] Executing {len(tasks)} task(s)..."
        )

        for i, task in enumerate(tasks):
            action = task.get("action", "")
            self._logger.info(
                f"[MotionExecutor] Task {i + 1}/{len(tasks)}: {action}"
            )

            success = self._dispatch_task(task)

            if not success:
                self._logger.error(
                    f"[MotionExecutor] Task {i + 1} ({action}) FAILED — aborting sequence."
                )
                return False

            self._logger.info(f"[MotionExecutor] Task {i + 1} ({action}) succeeded.")

        self._logger.info("[MotionExecutor] All tasks completed successfully.")
        return True

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def compliant_pick(self, task: dict, max_effort: float = 5.0) -> bool:
        """Pick with compliant (force-limited) gripper close instead of full close."""
        obj_id = task.get("object_id", "unknown")
        obj_x = float(task.get("object_x", 0.3))
        obj_y = float(task.get("object_y", 0.0))
        obj_z = float(task.get("object_z", 0.1))

        pregrasp = self._make_downward_pose(obj_x, obj_y, obj_z + PREGRASP_HEIGHT_OFFSET)
        if not self.move_to_pose(pregrasp):
            return False

        if not self.open_gripper():
            self._logger.warn("[MotionExecutor] Gripper open failed — continuing.")

        grasp = self._make_downward_pose(obj_x, obj_y, obj_z + 0.01)
        if not self.move_to_pose(grasp):
            return False

        self.compliant_close_gripper(max_effort=max_effort)

        if not self.move_to_pose(pregrasp):
            self._logger.warn("[MotionExecutor] Lift failed — continuing.")

        return True

    def _dispatch_task(self, task: dict) -> bool:
        """Route a single task dict to the appropriate executor method."""
        action = task.get("action", "")

        if action == "move_to_named_pose":
            pose_name = task.get("pose_name", "home")
            return self.move_to_named_pose("arm", pose_name)

        elif action == "open_gripper":
            return self.open_gripper()

        elif action == "close_gripper":
            return self.close_gripper()

        elif action == "pick":
            return self._execute_pick(task)

        elif action == "place":
            return self._execute_place(task)

        elif action == "move_relative":
            return self.move_relative(
                dx=float(task.get("dx", 0.0)),
                dy=float(task.get("dy", 0.0)),
                dz=float(task.get("dz", 0.0)),
            )

        else:
            self._logger.warn(f"[MotionExecutor] Unknown action '{action}' — skipping.")
            return True  # skip unknown actions gracefully

    def _execute_pick(self, task: dict) -> bool:
        """
        Execute a pick sequence:
        1. Move above the object (pre-grasp pose).
        2. Move down to grasp pose.
        3. Close gripper.
        4. Lift back up.

        Args:
            task: Dict with object_id, object_x, object_y, object_z.

        Returns:
            True on success.
        """
        obj_id = task.get("object_id", "unknown")
        obj_x = float(task.get("object_x", 0.3))
        obj_y = float(task.get("object_y", 0.0))
        obj_z = float(task.get("object_z", 0.1))

        self._logger.info(
            f"[MotionExecutor] pick: object={obj_id} at "
            f"({obj_x:.3f}, {obj_y:.3f}, {obj_z:.3f})"
        )

        # Pre-grasp: hover above object
        pregrasp_pose = self._make_downward_pose(
            obj_x, obj_y, obj_z + PREGRASP_HEIGHT_OFFSET
        )
        if not self.move_to_pose(pregrasp_pose):
            self._logger.error("[MotionExecutor] Failed to reach pre-grasp pose.")
            return False

        # Open gripper before descending
        if not self.open_gripper():
            self._logger.warn("[MotionExecutor] Gripper open failed — continuing anyway.")

        # Grasp pose: move down to object
        grasp_pose = self._make_downward_pose(obj_x, obj_y, obj_z + 0.01)
        if not self.move_to_pose(grasp_pose):
            self._logger.error("[MotionExecutor] Failed to reach grasp pose.")
            return False

        # Close gripper
        if not self.close_gripper():
            self._logger.warn("[MotionExecutor] Gripper close failed — continuing anyway.")

        # Lift back to pre-grasp height
        if not self.move_to_pose(pregrasp_pose):
            self._logger.warn("[MotionExecutor] Failed to lift after grasp — continuing.")

        return True

    def _execute_place(self, task: dict) -> bool:
        """
        Execute a place sequence:
        1. Move above the place position.
        2. Descend to place height.
        3. Open gripper.
        4. Retreat upward.

        Args:
            task: Dict with x, y, z.

        Returns:
            True on success.
        """
        place_x = float(task.get("x", 0.3))
        place_y = float(task.get("y", 0.0))
        place_z = float(task.get("z", DEFAULT_PLACE_Z))

        self._logger.info(
            f"[MotionExecutor] place at ({place_x:.3f}, {place_y:.3f}, {place_z:.3f})"
        )

        # Move above place location
        above_pose = self._make_downward_pose(
            place_x, place_y, place_z + PREGRASP_HEIGHT_OFFSET
        )
        if not self.move_to_pose(above_pose):
            self._logger.error("[MotionExecutor] Failed to reach pre-place pose.")
            return False

        # Descend
        place_pose = self._make_downward_pose(place_x, place_y, place_z)
        if not self.move_to_pose(place_pose):
            self._logger.error("[MotionExecutor] Failed to reach place pose.")
            return False

        # Open gripper to release
        if not self.open_gripper():
            self._logger.warn("[MotionExecutor] Gripper open failed during place.")

        # Retreat
        if not self.move_to_pose(above_pose):
            self._logger.warn("[MotionExecutor] Retreat after place failed — continuing.")

        return True

    @staticmethod
    def _make_downward_pose(x: float, y: float, z: float) -> PoseStamped:
        """
        Create a tool0 PoseStamped that puts the gripper's fingertip TCP,
        pointing straight down, at (x, y, z) in base_link.

        The orientation corresponds to a rotation where the tool z-axis
        points in the -world-Z direction (downward grasp).
        Quaternion for 180-degree rotation about X: (1, 0, 0, 0) rotated →
        q = (w=0, x=1, y=0, z=0) for pi rotation about X.

        move_to_pose() drives the "arm" group's IK tip link, tool0 — not the
        gripper's fingertip contact point — so z is offset by
        GRIPPER_TCP_OFFSET_Z here to compensate (see its definition above).

        Args:
            x, y, z: Desired gripper-TCP contact position in base_link (metres).

        Returns:
            PoseStamped ready for move_to_pose.
        """
        pose = PoseStamped()
        pose.header.frame_id = "base_link"
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z + GRIPPER_TCP_OFFSET_Z
        # End-effector pointing down: rotate 180 degrees about world X axis
        # q = (cos(pi/2), sin(pi/2)*x̂) = (0, 1, 0, 0) [w, x, y, z]
        pose.pose.orientation.x = 1.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 0.0
        return pose

    def _wait_for_future(self, future, timeout: float) -> bool:
        """Wait for a ROS 2 future from a background thread without touching the executor.

        Uses threading.Event so the main rclpy.spin() loop keeps running undisturbed.
        The done-callback fires inside the main executor and sets the event.
        """
        event = threading.Event()
        future.add_done_callback(lambda _: event.set())
        return event.wait(timeout=timeout)

    def _send_move_group_goal(
        self,
        goal: MoveGroupAction.Goal,
        timeout: float,
    ) -> bool:
        """Send a MoveGroup goal and wait for the result."""
        if not self._move_group_client.server_is_ready():
            self._logger.warn("MoveGroup server not ready — skipping.")
            return False

        send_goal_future = self._move_group_client.send_goal_async(goal)
        if not self._wait_for_future(send_goal_future, timeout):
            self._logger.error("send_goal timed out waiting for goal acceptance.")
            return False

        goal_handle = send_goal_future.result()
        if not goal_handle or not goal_handle.accepted:
            self._logger.error("MoveGroup goal was rejected.")
            return False

        result_future = goal_handle.get_result_async()
        if not self._wait_for_future(result_future, timeout):
            self._logger.error("MoveGroup result timed out.")
            return False

        result = result_future.result()
        error_code = result.result.error_code.val

        if error_code == MoveItErrorCodes.SUCCESS:
            return True

        self._logger.error(
            f"MoveGroup returned error code {error_code} "
            f"({self._moveit_error_name(error_code)})."
        )
        return False

    def _send_gripper_goal(
        self,
        position: float,
        max_effort: float,
        timeout: float,
    ) -> bool:
        """Send a GripperCommand goal and wait for the result."""
        if not self._gripper_client.server_is_ready():
            self._logger.warn("Gripper action server not ready — skipping.")
            return False

        goal = GripperCommand.Goal()
        goal.command.position = position
        goal.command.max_effort = max_effort

        send_goal_future = self._gripper_client.send_goal_async(goal)
        if not self._wait_for_future(send_goal_future, timeout):
            self._logger.error("Gripper send_goal timed out.")
            return False

        goal_handle = send_goal_future.result()
        if not goal_handle or not goal_handle.accepted:
            self._logger.error("Gripper goal was rejected.")
            return False

        result_future = goal_handle.get_result_async()
        if not self._wait_for_future(result_future, timeout):
            self._logger.error("Gripper result timed out.")
            return False

        result = result_future.result()
        if result.status == GoalStatus.STATUS_SUCCEEDED:
            return True

        self._logger.warn(
            f"Gripper action finished with status {result.status} — treating as success."
        )
        # Gripper controllers often report ABORTED even on success (stall detection);
        # treat any non-timeout completion as success.
        return True

    @staticmethod
    def _moveit_error_name(code: int) -> str:
        """Return a human-readable name for a MoveItErrorCodes value."""
        error_map = {
            MoveItErrorCodes.SUCCESS: "SUCCESS",
            MoveItErrorCodes.FAILURE: "FAILURE",
            MoveItErrorCodes.PLANNING_FAILED: "PLANNING_FAILED",
            MoveItErrorCodes.INVALID_MOTION_PLAN: "INVALID_MOTION_PLAN",
            MoveItErrorCodes.MOTION_PLAN_INVALIDATED_BY_ENVIRONMENT_CHANGE:
                "MOTION_PLAN_INVALIDATED_BY_ENVIRONMENT_CHANGE",
            MoveItErrorCodes.CONTROL_FAILED: "CONTROL_FAILED",
            MoveItErrorCodes.UNABLE_TO_AQUIRE_SENSOR_DATA: "UNABLE_TO_AQUIRE_SENSOR_DATA",
            MoveItErrorCodes.TIMED_OUT: "TIMED_OUT",
            MoveItErrorCodes.PREEMPTED: "PREEMPTED",
            MoveItErrorCodes.START_STATE_IN_COLLISION: "START_STATE_IN_COLLISION",
            MoveItErrorCodes.START_STATE_VIOLATES_PATH_CONSTRAINTS:
                "START_STATE_VIOLATES_PATH_CONSTRAINTS",
            MoveItErrorCodes.GOAL_IN_COLLISION: "GOAL_IN_COLLISION",
            MoveItErrorCodes.GOAL_VIOLATES_PATH_CONSTRAINTS:
                "GOAL_VIOLATES_PATH_CONSTRAINTS",
            MoveItErrorCodes.GOAL_CONSTRAINTS_VIOLATED: "GOAL_CONSTRAINTS_VIOLATED",
            MoveItErrorCodes.INVALID_GROUP_NAME: "INVALID_GROUP_NAME",
            MoveItErrorCodes.INVALID_GOAL_CONSTRAINTS: "INVALID_GOAL_CONSTRAINTS",
            MoveItErrorCodes.INVALID_ROBOT_STATE: "INVALID_ROBOT_STATE",
            MoveItErrorCodes.INVALID_LINK_NAME: "INVALID_LINK_NAME",
            MoveItErrorCodes.INVALID_OBJECT_NAME: "INVALID_OBJECT_NAME",
        }
        return error_map.get(code, f"UNKNOWN({code})")
