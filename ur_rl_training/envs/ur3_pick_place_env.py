"""
UR3 + Robotiq 2F-85 pick-and-place MuJoCo environment.

Matches the rl_policy_demo.world Gazebo scene exactly:
  - Table top at z=0.02, cube centre at z=0.045
  - Object spawn: x∈[0.22, 0.38], y∈[-0.15, 0.15]
  - Drop zone at x≈0.35, y≈0.20

Domain randomisation (every episode):
  - Object mass, friction, size (±20 %)
  - Observation noise (1 % std)
  - Initial joint jitter (±0.05 rad)

Obs (23-dim, matches shared_arm_policy_node / deployment node):
  qpos[6] + qvel[6] + ee_pos[3] + obj_pos[3] + drop_pos[3] + gripper[1] + phase[1]
"""

from pathlib import Path

import mujoco
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# ── paths ────────────────────────────────────────────────────────────────────
_PKG = Path(__file__).resolve().parents[1]
ARM_XML     = str(_PKG / "models" / "ur3" / "ur3.xml")
GRIPPER_XML = "/home/asimov/mujoco_menagerie/robotiq_2f85/2f85.xml"

# ── kinematics ───────────────────────────────────────────────────────────────
N_ARM  = 6
N_GRIP = 1
N_CTRL = N_ARM + N_GRIP

HOME_QPOS = np.array([-1.5708, -1.5708, 1.5708, -1.5708, -1.5708, 0.0])
GRASP_QPOS = np.array([-0.4,   -1.8,   2.2,   -2.0,   -1.57,  0.0])

# ── scene ────────────────────────────────────────────────────────────────────
TABLE_Z   = 0.02
OBJ_Z     = 0.045   # cube centre resting on table
LIFT_Z    = 0.10
OBJ_HALF  = 0.025   # default half-size

OBJ_X_RANGE  = (0.22, 0.38)
OBJ_Y_RANGE  = (-0.15, 0.15)
DROP_X_RANGE = (0.30, 0.40)
DROP_Y_RANGE = (0.15, 0.25)

# ── reward constants (same as ur_gazebo_single_arm_env with lift fixes) ──────
STEP_PENALTY           = 0.01
REACH_DELTA_GAIN       = 360.0
GRASP_DELTA_GAIN       = 420.0
LIFT_DELTA_GAIN        = 420.0
CARRY_DELTA_GAIN       = 360.0
REWARD_SCALE           = 100.0
GRASP_CLOSE_THRESHOLD  = 0.28
GRASP_LIFT_THRESHOLD   = 0.005   # lowered from 0.015 for easier streak entry
CARRY_HEIGHT_THRESHOLD = 0.02
GRASP_STREAK_STEPS     = 1
OBJECT_RESET_PENALTY   = 250.0


class UR3PickPlaceEnv(gym.Env):
    metadata = {"render_modes": ["human"], "render_fps": 50}

    def __init__(self, render_mode=None, curriculum_mode="grasp_focus",
                 domain_randomisation=True):
        self.render_mode          = render_mode
        self.curriculum_mode      = curriculum_mode
        self.domain_randomisation = domain_randomisation

        self._build_model(OBJ_HALF)

        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(23,), dtype=np.float32)
        self.action_space      = spaces.Box(-1.0, 1.0, shape=(N_CTRL,), dtype=np.float32)

        self._phase        = 0
        self._prev_dist    = None
        self._grasp_streak = 0
        self._grasped      = False
        self._drop_pos     = np.array([0.35, 0.20, TABLE_Z], dtype=np.float64)
        self._obj_init_pos = np.array([0.35, 0.0, OBJ_Z],    dtype=np.float64)
        self._viewer       = None

    # ── model construction ───────────────────────────────────────────────────
    def _build_model(self, obj_half=OBJ_HALF):
        spec    = mujoco.MjSpec.from_file(ARM_XML)
        gripper = mujoco.MjSpec.from_file(GRIPPER_XML)

        # attach gripper to arm at tool0 site
        att_site = next(s for s in spec.sites if s.name == "attachment_site")
        att_site.attach_body(gripper.worldbody.first_body(), "gripper-", "")

        # table
        tb  = spec.worldbody.add_body()
        tb.name = "table"
        tb.pos  = [0.35, 0.0, TABLE_Z / 2]
        tg = tb.add_geom()
        tg.type = mujoco.mjtGeom.mjGEOM_BOX
        tg.size = [0.30, 0.30, TABLE_Z / 2]
        tg.rgba = [0.7, 0.55, 0.35, 1.0]

        # object (free body)
        ob = spec.worldbody.add_body()
        ob.name = "object"
        ob.pos  = [0.35, 0.0, OBJ_Z]
        fj = ob.add_freejoint()
        fj.name = "object_joint"
        og = ob.add_geom()
        og.type     = mujoco.mjtGeom.mjGEOM_BOX
        og.size     = [obj_half, obj_half, obj_half]
        og.rgba     = [0.9, 0.1, 0.1, 1.0]
        og.friction = [3.0, 0.005, 0.0001]
        og.mass     = 0.1

        # drop-zone visual (no collision)
        dz  = spec.worldbody.add_body()
        dz.name = "drop_zone"
        dz.pos  = [0.35, 0.20, TABLE_Z + 0.001]
        dzg = dz.add_geom()
        dzg.type         = mujoco.mjtGeom.mjGEOM_CYLINDER
        dzg.size         = [0.06, 0.001, 0]
        dzg.rgba         = [0.1, 0.9, 0.1, 0.4]
        dzg.contype      = 0
        dzg.conaffinity  = 0

        self.model = spec.compile()
        self.data  = mujoco.MjData(self.model)

        # cache IDs
        self._ee_site   = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "attachment_site")
        self._obj_body  = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "object")
        self._drop_body = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "drop_zone")

        # gripper pad geoms for contact detection
        self._left_pads  = self._find_geoms([
            "gripper-left_pad1", "gripper-left_pad2",
            "gripper-right_pad1", "gripper-right_pad2",   # follower naming in 2f85
        ])
        self._right_pads = self._left_pads  # 2f85 symmetric — treat both as "pads"

        all_pads = set()
        for name in ["gripper-right_pad1", "gripper-right_pad2"]:
            gid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, name)
            if gid >= 0:
                all_pads.add(gid)
        left_pads = set()
        for name in ["gripper-left_pad1", "gripper-left_pad2"]:
            gid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, name)
            if gid >= 0:
                left_pads.add(gid)
        self._left_pads  = left_pads  if left_pads  else all_pads
        self._right_pads = all_pads   if all_pads   else left_pads

        self._obj_qpos_start = int(self.model.jnt_qposadr[
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "object_joint")])
        self._obj_geom_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "object_geom") \
                            if mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, "object_geom") >= 0 \
                            else -1
        # fallback: find obj geom by body
        if self._obj_geom_id < 0:
            for gi in range(self.model.ngeom):
                if self.model.geom_bodyid[gi] == self._obj_body and self.model.geom_type[gi] == mujoco.mjtGeom.mjGEOM_BOX:
                    self._obj_geom_id = gi
                    break

        # grip qpos address: right_driver_joint is first gripper actuated joint
        grip_jid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, "gripper-right_driver_joint")
        self._grip_qpos = int(self.model.jnt_qposadr[grip_jid]) if grip_jid >= 0 else N_ARM

    def _find_geoms(self, names):
        ids = set()
        for name in names:
            gid = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, name)
            if gid >= 0:
                ids.add(gid)
        return ids

    # ── domain randomisation ─────────────────────────────────────────────────
    def _randomise(self, rng):
        if not self.domain_randomisation:
            return
        # object mass
        self.model.body_mass[self._obj_body] = rng.uniform(0.05, 0.18)
        # object friction
        self.model.geom_friction[self._obj_geom_id] = [rng.uniform(1.0, 6.0), 0.005, 0.0001]

    # ── obs ──────────────────────────────────────────────────────────────────
    def _get_obs(self, noise=True):
        obs = np.concatenate([
            self.data.qpos[:N_ARM].astype(np.float32),
            self.data.qvel[:N_ARM].astype(np.float32),
            self.data.site_xpos[self._ee_site].astype(np.float32),
            self.data.xpos[self._obj_body].astype(np.float32),
            self._drop_pos.astype(np.float32),
            np.array([float(self.data.qpos[self._grip_qpos])], dtype=np.float32),
            np.array([float(self._phase)], dtype=np.float32),
        ])
        if noise and self.domain_randomisation:
            obs += self.np_random.normal(0, 0.005, size=obs.shape).astype(np.float32)
        return obs

    # ── contact ──────────────────────────────────────────────────────────────
    def _contact_state(self):
        left = right = False
        for ci in range(self.data.ncon):
            c = self.data.contact[ci]
            g1, g2 = int(c.geom1), int(c.geom2)
            other = None
            if   g1 == self._obj_geom_id: other = g2
            elif g2 == self._obj_geom_id: other = g1
            else: continue
            if other in self._left_pads:  left  = True
            if other in self._right_pads: right = True
            if left and right: break
        return left, right

    # ── reset ────────────────────────────────────────────────────────────────
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        self._randomise(self.np_random)

        ox = float(self.np_random.uniform(*OBJ_X_RANGE))
        oy = float(self.np_random.uniform(*OBJ_Y_RANGE))

        if self.curriculum_mode == "grasp_focus":
            ox     = float(self.np_random.uniform(0.25, 0.36))
            oy     = float(self.np_random.uniform(-0.08, 0.08))
            jitter = self.np_random.uniform(-0.05, 0.05, size=N_ARM)
            qstart = GRASP_QPOS + jitter
        else:
            qstart = HOME_QPOS + self.np_random.uniform(-0.05, 0.05, size=N_ARM)

        self.data.qpos[:N_ARM] = qstart
        self.data.ctrl[:N_ARM] = qstart
        self.data.ctrl[N_ARM]  = 0.0

        s = self._obj_qpos_start
        self.data.qpos[s:s+3]   = [ox, oy, OBJ_Z]
        self.data.qpos[s+3:s+7] = [1.0, 0.0, 0.0, 0.0]
        self._obj_init_pos = np.array([ox, oy, OBJ_Z], dtype=np.float64)

        dx = float(self.np_random.uniform(*DROP_X_RANGE))
        dy = float(self.np_random.uniform(*DROP_Y_RANGE))
        self._drop_pos = np.array([dx, dy, TABLE_Z], dtype=np.float64)
        self.model.body_pos[self._drop_body] = self._drop_pos

        self._phase        = 1 if self.curriculum_mode == "grasp_focus" else 0
        self._prev_dist    = None
        self._grasp_streak = 0
        self._grasped      = False

        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(noise=False), {}

    # ── step ─────────────────────────────────────────────────────────────────
    def step(self, action):
        arm_target = self.data.qpos[:N_ARM] + np.asarray(action[:N_ARM]) * 0.1
        arm_range  = self.model.actuator_ctrlrange[:N_ARM]
        self.data.ctrl[:N_ARM] = np.clip(arm_target, arm_range[:, 0], arm_range[:, 1])

        gl, gh = self.model.actuator_ctrlrange[N_ARM]
        # scale by (gh-gl)/20 so full action sweep = 5% of range per step,
        # reaching full close in ~20 steps — matches the [0,255] 2f85 actuator
        grip_delta = float(action[N_ARM]) * ((gh - gl) / 20.0)
        self.data.ctrl[N_ARM] = float(np.clip(self.data.ctrl[N_ARM] + grip_delta, gl, gh))

        for _ in range(5):
            mujoco.mj_step(self.model, self.data)

        reward, terminated = self._reward()

        obj = self.data.xpos[self._obj_body].copy()
        if obj[2] < -0.05 or np.linalg.norm(obj[:2] - np.array([0.35, 0.0])) > 1.0:
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

    # ── reward ───────────────────────────────────────────────────────────────
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
        any_c    = left_c or right_c
        both_c   = left_c and right_c
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
            if ee_to_obj < 0.10: reward += 18.0 * (1.0 - ee_to_obj / 0.10)
            if ee_to_obj_xy < 0.05: reward += 14.0 * (1.0 - ee_to_obj_xy / 0.05)
            if any_c:   reward += 24.0
            if both_c:  reward += 42.0
            if grip > 0.55 and not any_c: reward -= 3.0
            if grip < 0.15 and ee_to_obj < 0.05: reward -= 4.0
            if grip > GRASP_CLOSE_THRESHOLD and any_c:
                reward += max(0.0, obj_lift) * 1300.0
                if both_c:
                    reward += 36.0
                    reward += (grip - GRASP_CLOSE_THRESHOLD) * 60.0  # push gripper to close harder
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
            if dist_z < 0.08: reward += 14.0 * (1.0 - dist_z / 0.08)
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
                if obj_to_drop_xy < 0.10: reward += 40.0 * (1.0 - obj_to_drop_xy / 0.10)
                if obj_to_drop_xy < 0.08:
                    reward += 120.0           # strong signal for being over drop zone
                    if grip < 0.35: reward += 80.0 * (1.0 - grip / 0.35)  # reward releasing
            else:
                reward -= 8.0
            if not carrying and obj_lift < GRASP_LIFT_THRESHOLD and obj_to_drop_xy > 0.12:
                reward -= 60.0
                self._grasped = False; self._grasp_streak = 0
                self._phase = 1; self._prev_dist = None
            # loosened grip threshold: 0.35 (was 0.1) so partial release counts
            if obj_to_drop_xy < 0.08 and grip < 0.35 and obj[2] < init[2] + 0.03:
                self._grasped = False
                reward += 1800.0
                terminated = True

        reward -= joint_vel_pen
        return float(reward / REWARD_SCALE), terminated

    # ── render ───────────────────────────────────────────────────────────────
    def render(self):
        if self.render_mode == "human":
            if self._viewer is None:
                self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self._viewer.sync()

    def close(self):
        if self._viewer:
            self._viewer.close()
            self._viewer = None
