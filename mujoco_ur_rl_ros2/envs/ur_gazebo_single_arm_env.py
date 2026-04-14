"""
Single-arm pick-and-place env matching the Gazebo colored_blocks world.

Arm base at origin (0,0,0), euler_z=0 — so local frame == world frame.
The shared_arm_policy_node.py can run the trained model directly by passing
world-frame object/drop coords as parameters (no frame transform needed).

Obs (23-dim, same format as shared_arm training):
  qpos[6] + qvel[6] + ee_pos[3] + obj_pos[3] + drop_pos[3] + gripper[1] + phase[1]

Actions (7-dim): 6 arm joint deltas + 1 gripper delta  (same as shared_arm model)

Phase-based reward (mirrors ur_dual_arm_env phases):
  0=reach  1=grasp  2=lift  3=place
"""

import numpy as np
import mujoco
import gymnasium as gym
from gymnasium import spaces

ARM_MODEL_PATH   = "/home/asimov/mujoco_menagerie/universal_robots_ur5e/ur5e.xml"
GRIPPER_MODEL_PATH = "/home/asimov/mujoco_menagerie/robotiq_2f85/2f85.xml"

N_ARM   = 6
N_GRIP  = 1
N_CTRL  = N_ARM + N_GRIP

# Randomisation ranges (world frame == local frame, arm at origin)
OBJ_X_RANGE  = (0.28, 0.45)
OBJ_Y_RANGE  = (-0.15, 0.15)
OBJ_Z        = 0.045
DROP_X_RANGE = (0.28, 0.45)
DROP_Y_RANGE = (0.15, 0.28)   # always in front-left quadrant
DROP_Z       = 0.025

GRASP_HEIGHT  = 0.10   # lift target above table
READY_POSE    = np.array([0.0, -1.0, 1.5, -1.57, -1.57, 0.0], dtype=np.float64)

# Phase transition thresholds
REACH_XY_THRESH = 0.06
REACH_Z_THRESH  = 0.04
GRASP_CLOSE     = 0.60   # fraction of max gripper
GRASP_EE_THRESH = 0.05
LIFT_THRESH     = 0.05
PLACE_THRESH    = 0.08

# Reward weights
DELTA_GAIN     = 100.0
PENALTY_GAIN   = 300.0
PHASE_BONUSES  = [100.0, 1000.0, 200.0, 1000.0]   # reach→grasp→lift→place


class URGazeboSingleArmEnv(gym.Env):
    """Single UR5e at origin, pick-and-place, 23-dim obs matching shared_arm_policy."""

    metadata = {"render_modes": ["human"], "render_fps": 50}

    def __init__(self, render_mode=None, curriculum_mode="easy_grasp"):
        self.render_mode  = render_mode
        self.curriculum_mode = curriculum_mode

        # ── build MuJoCo model ───────────────────────────────────────────
        spec = mujoco.MjSpec.from_file(ARM_MODEL_PATH)
        grip = mujoco.MjSpec.from_file(GRIPPER_MODEL_PATH)
        spec.sites[0].attach_body(grip.worldbody.first_body(), "gripper-", "")

        # table
        tb = spec.worldbody.add_body()
        tb.name = "table"
        tb.pos  = [0.35, 0.0, 0.0]
        tg = tb.add_geom()
        tg.type = mujoco.mjtGeom.mjGEOM_BOX
        tg.size = [0.25, 0.25, 0.02]
        tg.rgba = [0.8, 0.6, 0.4, 1.0]

        # object
        ob = spec.worldbody.add_body()
        ob.name = "object"
        ob.pos  = [0.35, 0.0, OBJ_Z]
        fj = ob.add_freejoint(); fj.name = "object_joint"
        og = ob.add_geom()
        og.type     = mujoco.mjtGeom.mjGEOM_BOX
        og.size     = [0.025, 0.025, 0.025]
        og.rgba     = [0.9, 0.1, 0.1, 1.0]
        og.friction = [1.5, 0.005, 0.0001]
        og.mass     = 0.1

        # drop zone marker (no collision)
        dz = spec.worldbody.add_body()
        dz.name = "drop_zone"
        dz.pos  = [0.35, 0.20, DROP_Z]
        dzg = dz.add_geom()
        dzg.type        = mujoco.mjtGeom.mjGEOM_CYLINDER
        dzg.size        = [0.05, 0.002, 0]
        dzg.rgba        = [0.1, 0.9, 0.1, 0.4]
        dzg.contype     = 0
        dzg.conaffinity = 0

        self.model = spec.compile()
        self.data  = mujoco.MjData(self.model)

        self._ee_site_id   = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE,  "attachment_site")
        self._obj_body_id  = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY,  "object")
        self._drop_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY,  "drop_zone")
        self._grip_qpos_start = N_ARM   # qpos[6] = right_driver_joint (main actuated gripper joint)
        # Robotiq 2F-85 has 8 gripper qpos slots (6 arm + 8 gripper = 14) then freejoint
        self._obj_qpos_start  = self.model.jnt_qposadr[
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "object_joint")
        ]

        # obs/act spaces
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(23,), dtype=np.float32)
        self.action_space      = spaces.Box(-1.0, 1.0, shape=(N_CTRL,), dtype=np.float32)

        self._phase      = 0
        self._prev_dist  = None
        self._drop_pos   = np.array([0.35, 0.20, DROP_Z], dtype=np.float64)
        self._viewer     = None

    # ── helpers ─────────────────────────────────────────────────────────
    def _ee_pos(self):  return self.data.site_xpos[self._ee_site_id].copy()
    def _obj_pos(self): return self.data.xpos[self._obj_body_id].copy()
    def _gripper(self): return float(self.data.qpos[self._grip_qpos_start])

    def _get_obs(self):
        qpos    = self.data.qpos[:N_ARM].astype(np.float32)
        qvel    = self.data.qvel[:N_ARM].astype(np.float32)
        ee      = self._ee_pos().astype(np.float32)
        obj     = self._obj_pos().astype(np.float32)
        drop    = self._drop_pos.astype(np.float32)
        gripper = np.array([self._gripper()], dtype=np.float32)
        phase   = np.array([float(self._phase)], dtype=np.float32)
        return np.concatenate([qpos, qvel, ee, obj, drop, gripper, phase])

    def _max_grip(self):
        idx = self.model.actuator_ctrlrange[N_ARM]
        return float(idx[1]) if idx is not None else 0.8

    # ── reset ────────────────────────────────────────────────────────────
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        # arm to ready pose
        self.data.qpos[:N_ARM] = READY_POSE
        self.data.ctrl[:N_ARM] = READY_POSE
        self.data.ctrl[N_ARM]  = 0.0

        # randomise object
        ox = self.np_random.uniform(*OBJ_X_RANGE)
        oy = self.np_random.uniform(*OBJ_Y_RANGE)
        s = self._obj_qpos_start
        self.data.qpos[s:s+3]   = [ox, oy, OBJ_Z]
        self.data.qpos[s+3:s+7] = [1, 0, 0, 0]

        # randomise drop zone
        dx = self.np_random.uniform(*DROP_X_RANGE)
        dy = self.np_random.uniform(*DROP_Y_RANGE)
        self._drop_pos = np.array([dx, dy, DROP_Z], dtype=np.float64)
        self.model.body_pos[self._drop_body_id] = self._drop_pos

        phase_start = 1 if self.curriculum_mode == "grasp_focus" else 0
        self._phase     = phase_start
        self._prev_dist = None

        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    # ── step ─────────────────────────────────────────────────────────────
    def step(self, action):
        arm_delta = np.clip(action[:N_ARM], -1.0, 1.0) * 0.05
        self.data.ctrl[:N_ARM] = np.clip(
            self.data.ctrl[:N_ARM] + arm_delta,
            self.model.actuator_ctrlrange[:N_ARM, 0],
            self.model.actuator_ctrlrange[:N_ARM, 1],
        )
        grip_delta = float(np.clip(action[N_ARM], -1.0, 1.0)) * 0.02
        self.data.ctrl[N_ARM] = float(np.clip(
            self.data.ctrl[N_ARM] + grip_delta, 0.0, self._max_grip()
        ))

        for _ in range(5):
            mujoco.mj_step(self.model, self.data)

        ee   = self._ee_pos()
        obj  = self._obj_pos()
        drop = self._drop_pos
        grip = self._gripper()
        grip_frac = grip / max(self._max_grip(), 1e-6)

        reward, terminated = self._shaped_reward(ee, obj, drop, grip, grip_frac)
        truncated = bool(self.data.time > 20.0)

        # phase transitions
        self._advance_phase(ee, obj, drop, grip_frac)

        if self.render_mode == "human":
            self.render()

        return self._get_obs(), reward, terminated, truncated, {"phase": self._phase}

    def _shaped_reward(self, ee, obj, drop, grip, grip_frac):
        reward     = 0.0
        terminated = False

        if self._phase == 0:   # reach
            dist = np.linalg.norm(ee[:2] - obj[:2])
            if self._prev_dist is not None:
                delta = self._prev_dist - dist
                reward += DELTA_GAIN * delta if delta > 0 else PENALTY_GAIN * delta
            self._prev_dist = dist
            if grip_frac > 0.1:
                reward -= 5.0   # penalise closing gripper during approach

        elif self._phase == 1:  # grasp
            dist = np.linalg.norm(ee - obj)
            reward += 2.0 * max(0, 0.10 - dist)
            reward += 5.0 * grip_frac if dist < 0.05 else -5.0 * grip_frac

        elif self._phase == 2:  # lift
            lift_target = obj[2] + GRASP_HEIGHT
            dist = abs(ee[2] - lift_target)
            if self._prev_dist is not None:
                delta = self._prev_dist - dist
                reward += DELTA_GAIN * delta if delta > 0 else PENALTY_GAIN * delta
            self._prev_dist = dist
            if grip_frac < 0.5:
                reward -= 20.0   # penalise dropping

        elif self._phase == 3:  # place
            dist = np.linalg.norm(obj[:2] - drop[:2])
            if self._prev_dist is not None:
                delta = self._prev_dist - dist
                reward += DELTA_GAIN * delta if delta > 0 else PENALTY_GAIN * delta
            self._prev_dist = dist
            if dist < PLACE_THRESH and grip_frac < 0.2:
                reward    += PHASE_BONUSES[3]
                terminated = True

        return reward, terminated

    def _advance_phase(self, ee, obj, drop, grip_frac):
        if self._phase == 0:
            xy_ok = np.linalg.norm(ee[:2] - obj[:2]) < REACH_XY_THRESH
            z_ok  = abs(ee[2] - obj[2]) < REACH_Z_THRESH * 2
            if xy_ok and z_ok:
                self._phase = 1
                self._prev_dist = None
                return

        if self._phase == 1:
            grasped = grip_frac > GRASP_CLOSE and np.linalg.norm(ee - obj) < GRASP_EE_THRESH
            if grasped:
                self._phase = 2
                self._prev_dist = None
                return

        if self._phase == 2:
            lift_ok = ee[2] > (obj[2] + GRASP_HEIGHT - LIFT_THRESH)
            if lift_ok:
                self._phase = 3
                self._prev_dist = None
                return

    # ── render ───────────────────────────────────────────────────────────
    def render(self):
        if self.render_mode == "human":
            if self._viewer is None:
                self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self._viewer.sync()

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
