"""
Single-arm pick-and-place env matching the Gazebo colored_blocks world.

Arm base at origin (0,0,0), euler_z=0 — local frame == world frame.
Uses the same proven reward structure as ur_dual_arm_env.py.

Obs (23-dim, matches shared_arm_policy_node):
  qpos[6] + qvel[6] + ee_pos[3] + obj_pos[3] + drop_pos[3] + gripper[1] + phase[1]

Actions (7-dim): 6 arm joint targets (relative to ready_pose) + 1 gripper
"""

import mujoco
import numpy as np
import gymnasium as gym
from gymnasium import spaces

ARM_MODEL_PATH    = "/home/asimov/mujoco_menagerie/universal_robots_ur5e/ur5e.xml"
GRIPPER_MODEL_PATH = "/home/asimov/mujoco_menagerie/robotiq_2f85/2f85.xml"

N_ARM  = 6
N_GRIP = 1
N_CTRL = N_ARM + N_GRIP

READY_POSE     = np.array([0.0, -1.0, 1.5, -1.57, -1.57, 0.0], dtype=np.float64)
ARM_ACT_SCALE  = np.array([2.0, 1.8, 2.0, 1.8, 1.6, 1.6],      dtype=np.float64)

OBJ_X_RANGE  = (0.28, 0.45)
OBJ_Y_RANGE  = (-0.15, 0.15)
OBJ_Z        = 0.045
DROP_X_RANGE = (0.28, 0.45)
DROP_Y_RANGE = (0.15, 0.28)
DROP_Z       = 0.025
LIFT_Z       = 0.10

# Reward constants (mirrored from ur_dual_arm_env)
STEP_PENALTY           = 0.01
REACH_DELTA_GAIN       = 360.0
GRASP_DELTA_GAIN       = 420.0
LIFT_DELTA_GAIN        = 420.0
CARRY_DELTA_GAIN       = 280.0
REWARD_SCALE           = 100.0
GRASP_CLOSE_THRESHOLD  = 0.28
GRASP_LIFT_THRESHOLD   = 0.015
CARRY_HEIGHT_THRESHOLD = 0.02
GRASP_STREAK_STEPS     = 1
OBJECT_RESET_PENALTY   = 250.0


class URGazeboSingleArmEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 50}

    def __init__(self, render_mode=None, curriculum_mode="easy_grasp"):
        self.render_mode    = render_mode
        self.curriculum_mode = curriculum_mode

        # ── build model ─────────────────────────────────────────────────
        spec = mujoco.MjSpec.from_file(ARM_MODEL_PATH)
        grip = mujoco.MjSpec.from_file(GRIPPER_MODEL_PATH)
        spec.sites[0].attach_body(grip.worldbody.first_body(), "gripper-", "")

        tb = spec.worldbody.add_body(); tb.name = "table"; tb.pos = [0.35, 0.0, 0.0]
        tg = tb.add_geom(); tg.type = mujoco.mjtGeom.mjGEOM_BOX
        tg.size = [0.25, 0.25, 0.02]; tg.rgba = [0.8, 0.6, 0.4, 1.0]

        ob = spec.worldbody.add_body(); ob.name = "object"; ob.pos = [0.35, 0.0, OBJ_Z]
        fj = ob.add_freejoint(); fj.name = "object_joint"
        og = ob.add_geom(); og.type = mujoco.mjtGeom.mjGEOM_BOX
        og.size = [0.025, 0.025, 0.025]; og.rgba = [0.9, 0.1, 0.1, 1.0]
        og.friction = [1.5, 0.005, 0.0001]; og.mass = 0.1

        dz = spec.worldbody.add_body(); dz.name = "drop_zone"; dz.pos = [0.35, 0.20, DROP_Z]
        dzg = dz.add_geom(); dzg.type = mujoco.mjtGeom.mjGEOM_CYLINDER
        dzg.size = [0.05, 0.002, 0]; dzg.rgba = [0.1, 0.9, 0.1, 0.4]
        dzg.contype = 0; dzg.conaffinity = 0

        self.model = spec.compile()
        self.data  = mujoco.MjData(self.model)

        # ── cache IDs ────────────────────────────────────────────────────
        self._ee_site   = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "attachment_site")
        self._obj_body  = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "object")
        self._drop_body = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "drop_zone")
        self._obj_geom  = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "object_geom" if
                          mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "object_geom") >= 0
                          else "object_geom")

        # gripper pad geoms for contact detection
        self._left_pad_geoms  = self._find_geoms(["gripper-left_pad1",  "gripper-left_pad2"])
        self._right_pad_geoms = self._find_geoms(["gripper-right_pad1", "gripper-right_pad2"])

        self._obj_qpos_start = int(self.model.jnt_qposadr[
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "object_joint")])
        self._grip_qpos = N_ARM  # qpos[6] = right_driver_joint

        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(23,), dtype=np.float32)
        self.action_space      = spaces.Box(-1.0, 1.0, shape=(N_CTRL,), dtype=np.float32)

        self._phase       = 0
        self._prev_dist   = None
        self._grasp_streak = 0
        self._grasped     = False
        self._drop_pos    = np.array([0.35, 0.20, DROP_Z], dtype=np.float64)
        self._obj_init_pos = np.array([0.35, 0.0, OBJ_Z],  dtype=np.float64)
        self._viewer      = None

    def _find_geoms(self, names):
        ids = set()
        for name in names:
            gid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, name)
            if gid >= 0:
                ids.add(gid)
        return ids

    # ── obs ──────────────────────────────────────────────────────────────
    def _get_obs(self):
        return np.concatenate([
            self.data.qpos[:N_ARM].astype(np.float32),
            self.data.qvel[:N_ARM].astype(np.float32),
            self.data.site_xpos[self._ee_site].astype(np.float32),
            self.data.xpos[self._obj_body].astype(np.float32),
            self._drop_pos.astype(np.float32),
            np.array([float(self.data.qpos[self._grip_qpos])], dtype=np.float32),
            np.array([float(self._phase)], dtype=np.float32),
        ])

    # ── contact ──────────────────────────────────────────────────────────
    def _contact_state(self):
        left = right = False
        for ci in range(self.data.ncon):
            c = self.data.contact[ci]
            g1, g2 = int(c.geom1), int(c.geom2)
            other = None
            if g1 == self._obj_geom:  other = g2
            elif g2 == self._obj_geom: other = g1
            else: continue
            if other in self._left_pad_geoms:  left  = True
            if other in self._right_pad_geoms: right = True
            if left and right: break
        return left, right

    # ── reset ────────────────────────────────────────────────────────────
    def reset(self, seed=None, options=None):  # noqa: ARG002
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        self.data.qpos[:N_ARM] = READY_POSE
        self.data.ctrl[:N_ARM] = READY_POSE
        self.data.ctrl[N_ARM]  = 0.0

        ox = float(self.np_random.uniform(*OBJ_X_RANGE))
        oy = float(self.np_random.uniform(*OBJ_Y_RANGE))
        if self.curriculum_mode == "grasp_focus":
            ox = float(self.np_random.uniform(0.30, 0.40))
            oy = float(self.np_random.uniform(-0.05, 0.05))
        s = self._obj_qpos_start
        self.data.qpos[s:s+3]   = [ox, oy, OBJ_Z]
        self.data.qpos[s+3:s+7] = [1.0, 0.0, 0.0, 0.0]
        self._obj_init_pos = np.array([ox, oy, OBJ_Z], dtype=np.float64)

        dx = float(self.np_random.uniform(*DROP_X_RANGE))
        dy = float(self.np_random.uniform(*DROP_Y_RANGE))
        self._drop_pos = np.array([dx, dy, DROP_Z], dtype=np.float64)
        self.model.body_pos[self._drop_body] = self._drop_pos

        self._phase        = 1 if self.curriculum_mode == "grasp_focus" else 0
        self._prev_dist    = None
        self._grasp_streak = 0
        self._grasped      = False

        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    # ── step ─────────────────────────────────────────────────────────────
    def step(self, action):
        # arm: position target relative to ready pose
        arm_target = READY_POSE + np.asarray(action[:N_ARM], dtype=np.float64) * ARM_ACT_SCALE
        arm_range  = self.model.actuator_ctrlrange[:N_ARM]
        self.data.ctrl[:N_ARM] = np.clip(arm_target, arm_range[:, 0], arm_range[:, 1])

        # gripper: map [-1,1] → [low, high]
        gl, gh = self.model.actuator_ctrlrange[N_ARM]
        grip_cmd = (float(action[N_ARM]) + 1.0) / 2.0
        self.data.ctrl[N_ARM] = gl + grip_cmd * (gh - gl)

        for _ in range(5):
            mujoco.mj_step(self.model, self.data)

        reward, terminated = self._reward()

        # reset object if it falls off table
        obj = self.data.xpos[self._obj_body].copy()
        if obj[2] < -0.05 or np.linalg.norm(obj[:2]) > 1.5:
            reward -= OBJECT_RESET_PENALTY / REWARD_SCALE
            s = self._obj_qpos_start
            self.data.qpos[s:s+3]   = self._obj_init_pos
            self.data.qpos[s+3:s+7] = [1.0, 0.0, 0.0, 0.0]
            mujoco.mj_forward(self.model, self.data)
            self._phase = 0; self._prev_dist = None; self._grasp_streak = 0

        truncated = bool(self.data.time > 20.0)
        if self.render_mode == "human":
            self.render()
        return self._get_obs(), reward, terminated, truncated, {"phase": self._phase}

    # ── reward (mirrors ur_dual_arm_env._arm_reward) ─────────────────────
    def _reward(self):
        ee   = self.data.site_xpos[self._ee_site].copy()
        obj  = self.data.xpos[self._obj_body].copy()
        drop = self._drop_pos
        init = self._obj_init_pos
        grip = float(self.data.qpos[self._grip_qpos])

        ee_to_obj      = float(np.linalg.norm(ee - obj))
        ee_to_obj_xy   = float(np.linalg.norm(ee[:2] - obj[:2]))
        ee_height_err  = float(abs(ee[2] - (obj[2] + 0.03)))
        obj_to_drop_xy = float(np.linalg.norm(obj[:2] - drop[:2]))
        obj_lift       = float(obj[2] - init[2])
        joint_vel_pen  = 0.01 * float(np.sum(np.abs(self.data.qvel[:N_ARM])))

        left_c, right_c = self._contact_state()
        any_c   = left_c or right_c
        both_c  = left_c and right_c
        carrying = grip > GRASP_CLOSE_THRESHOLD and (
            both_c or (obj_lift > CARRY_HEIGHT_THRESHOLD and ee_to_obj < 0.12)
        )

        reward     = -STEP_PENALTY
        terminated = False
        phase      = self._phase

        if phase == 0:
            dist = ee_to_obj
            reward += 4.5 / (1.0 + dist * 10.0)
            reward += 7.0 / (1.0 + ee_to_obj_xy * 18.0)
            if ee_height_err < 0.06:
                reward += 6.0 * (1.0 - ee_height_err / 0.06)
            if self._prev_dist is not None:
                delta = self._prev_dist - dist
                reward += delta * REACH_DELTA_GAIN if delta > 0 else delta * 90.0
            self._prev_dist = dist
            if ee_to_obj < 0.15:
                reward += 12.0 * (1.0 - ee_to_obj / 0.15)
            if ee_to_obj_xy < 0.07 and ee_height_err < 0.035:
                reward += 18.0
            if grip > 0.45 and ee_to_obj > 0.15:
                reward -= 2.0
            if any_c:
                reward += 30.0
                self._phase = 1; self._prev_dist = None
            elif ee_to_obj < 0.08 or (ee_to_obj_xy < 0.06 and ee_height_err < 0.03):
                reward += 120.0
                self._phase = 1; self._prev_dist = None

        elif phase == 1:
            reward += 6.0 / (1.0 + ee_to_obj * 10.0)
            reward += 10.0 / (1.0 + ee_to_obj_xy * 18.0)
            if self._prev_dist is not None:
                delta = self._prev_dist - ee_to_obj
                reward += delta * GRASP_DELTA_GAIN if delta > 0 else delta * 80.0
            self._prev_dist = ee_to_obj
            if ee_to_obj < 0.10:
                reward += 18.0 * (1.0 - ee_to_obj / 0.10)
            if ee_to_obj_xy < 0.05:
                reward += 14.0 * (1.0 - ee_to_obj_xy / 0.05)
            if any_c:  reward += 24.0
            if both_c: reward += 42.0
            if grip > 0.55 and not any_c: reward -= 3.0
            if grip < 0.15 and ee_to_obj < 0.05: reward -= 4.0
            if grip > GRASP_CLOSE_THRESHOLD and any_c:
                reward += max(0.0, obj_lift) * 1300.0
                if both_c: reward += 36.0
                if obj_lift > GRASP_LIFT_THRESHOLD:
                    reward += 75.0
                    self._grasp_streak += 1
                    reward += 12.0 * self._grasp_streak
                else:
                    self._grasp_streak = 0
            else:
                self._grasp_streak = 0
            if self._grasp_streak >= GRASP_STREAK_STEPS and carrying:
                self._grasped = True
                self._phase = 2; self._prev_dist = None
                reward += 900.0

        elif phase == 2:
            dist_z = abs(obj[2] - LIFT_Z)
            if self._prev_dist is not None:
                delta = self._prev_dist - dist_z
                reward += delta * LIFT_DELTA_GAIN if delta > 0 else delta * 100.0
            self._prev_dist = dist_z
            reward += max(0.0, obj_lift) * 340.0
            reward += 28.0 if carrying else -15.0
            if dist_z < 0.08:
                reward += 14.0 * (1.0 - dist_z / 0.08)
            if not carrying and obj_lift < GRASP_LIFT_THRESHOLD:
                reward -= 60.0
                self._grasped = False; self._grasp_streak = 0
                self._phase = 1; self._prev_dist = None
            if carrying and dist_z < 0.05 and obj_lift > CARRY_HEIGHT_THRESHOLD:
                self._phase = 3; self._prev_dist = None
                reward += 320.0

        elif phase == 3:
            if self._prev_dist is not None:
                delta = self._prev_dist - obj_to_drop_xy
                reward += delta * CARRY_DELTA_GAIN if delta > 0 else delta * 70.0
            self._prev_dist = obj_to_drop_xy
            if carrying:
                reward += 10.0 / (1.0 + obj_to_drop_xy * 10.0)
                if obj_to_drop_xy < 0.10:
                    reward += 40.0 * (1.0 - obj_to_drop_xy / 0.10)
                if obj_to_drop_xy < 0.08 and grip < 0.2:
                    reward += 70.0
            else:
                reward -= 20.0
            if not carrying and obj_lift < GRASP_LIFT_THRESHOLD and obj_to_drop_xy > 0.12:
                reward -= 60.0
                self._grasped = False; self._grasp_streak = 0
                self._phase = 1; self._prev_dist = None
            if obj_to_drop_xy < 0.08 and grip < 0.1 and obj[2] < init[2] + 0.015:
                self._grasped = False
                reward += 1800.0
                terminated = True

        reward -= joint_vel_pen
        return float(reward / REWARD_SCALE), terminated

    # ── render ───────────────────────────────────────────────────────────
    def render(self):
        if self.render_mode == "human":
            if self._viewer is None:
                self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self._viewer.sync()

    def close(self):
        if self._viewer:
            self._viewer.close()
            self._viewer = None
