import numpy as np
import mujoco
import mujoco.viewer
import gymnasium as gym
from gymnasium import spaces

TABLE_Z = 0.02
OBJECT_Z = 0.045
LIFT_Z = 0.10
Y_SPACING = 1.0
GRASP_LIFT_THRESHOLD = 0.015
CARRY_HEIGHT_THRESHOLD = 0.02
GRASP_CLOSE_THRESHOLD = 0.28
GRASP_STREAK_STEPS = 1
STEP_PENALTY = 0.01
OBJECT_RESET_X_MARGIN = 0.25
OBJECT_RESET_Y_MARGIN = 0.25
OBJECT_RESET_Z_MIN = 0.0
OBJECT_RESET_Z_MAX = 0.5
OBJECT_RESET_PENALTY = 250.0
OBJECT_MASS = 0.25
REACH_DELTA_GAIN = 360.0
GRASP_DELTA_GAIN = 420.0
LIFT_DELTA_GAIN = 420.0
CARRY_DELTA_GAIN = 280.0
REWARD_SCALE = 100.0
ARM_ACTION_SCALE = np.array([2.0, 1.8, 2.0, 1.8, 1.6, 1.6], dtype=np.float64)
CURRICULUM_MODES = {"none", "easy_grasp", "grasp_focus"}

ARM_MODEL_PATH = "/home/asimov/mujoco_menagerie/universal_robots_ur5e/ur5e.xml"
GRIPPER_MODEL_PATH = "/home/asimov/mujoco_menagerie/robotiq_2f85/2f85.xml"

SIDE_CFG = {
    "left": {
        "base_x": -0.9,
        "table_x": -1.18,
        "drop_x": -1.25,
        "euler_z": 180.0,
        "ready_pose": np.array([0.0, -1.0, 1.5, -1.57, -1.57, 0.0], dtype=np.float64),
    },
    "right": {
        "base_x": 0.9,
        "table_x": 1.18,
        "drop_x": 1.25,
        "euler_z": 0.0,
        "ready_pose": np.array([0.0, -1.0, 1.5, -1.57, -1.57, 0.0], dtype=np.float64),
    },
}

OBJECT_COLORS = [
    [0.9, 0.1, 0.1, 1.0],
    [0.1, 0.1, 0.9, 1.0],
    [0.1, 0.8, 0.1, 1.0],
    [0.9, 0.8, 0.1, 1.0],
    [0.9, 0.2, 0.8, 1.0],
    [0.1, 0.8, 0.8, 1.0],
    [0.95, 0.45, 0.1, 1.0],
    [0.5, 0.9, 0.1, 1.0],
]

def _centered_y_positions(count_per_side):
    offset = (count_per_side - 1) / 2.0
    return [float((idx - offset) * Y_SPACING) for idx in range(count_per_side)]


def _build_arm_cfg(arm_count):
    if arm_count < 2 or arm_count % 2 != 0:
        raise ValueError("arm_count must be an even number >= 2")

    cfg = []
    y_positions = _centered_y_positions(arm_count // 2)

    for side in ("left", "right"):
        side_cfg = SIDE_CFG[side]
        for arm_idx, y_pos in enumerate(y_positions, start=1):
            color_idx = len(cfg) % len(OBJECT_COLORS)
            name = f"{side}{arm_idx}"
            cfg.append(
                {
                    "name": name,
                    "side": side,
                    "base_pos": [side_cfg["base_x"], y_pos, 0.0],
                    "euler_z": side_cfg["euler_z"],
                    "table_pos": [side_cfg["table_x"], y_pos],
                    "table_size": [0.28, 0.20],
                    "obj_pos": [side_cfg["table_x"], y_pos, OBJECT_Z],
                    "obj_color": OBJECT_COLORS[color_idx],
                    "drop_pos": [side_cfg["drop_x"], y_pos, TABLE_Z],
                    "ready_pose": side_cfg["ready_pose"].copy(),
                }
            )

    return cfg


class URDualArmEnv(gym.Env):
    """
    Symmetric multi-arm UR5e task.
    Each arm gets its own table, object, and drop zone.
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(self, render_mode=None, arm_count=4, curriculum_mode="none"):
        if curriculum_mode not in CURRICULUM_MODES:
            raise ValueError(f"curriculum_mode must be one of {sorted(CURRICULUM_MODES)}")

        self.render_mode = render_mode
        self.curriculum_mode = curriculum_mode
        self.arm_cfg = _build_arm_cfg(arm_count)

        spec = mujoco.MjSpec()
        spec.option.gravity = [0, 0, -9.81]

        tex = spec.add_texture()
        tex.name = "groundplane"
        tex.type = mujoco.mjtTexture.mjTEXTURE_2D
        tex.builtin = mujoco.mjtBuiltin.mjBUILTIN_CHECKER
        tex.rgb1 = [0.2, 0.3, 0.4]
        tex.rgb2 = [0.1, 0.2, 0.3]
        tex.width = 300
        tex.height = 300

        mat = spec.add_material()
        mat.name = "groundplane"
        mat.textures = ["groundplane"] + [""] * 9
        mat.texuniform = True

        floor = spec.worldbody.add_geom()
        floor.name = "floor"
        floor.type = mujoco.mjtGeom.mjGEOM_PLANE
        floor.size = [0, 0, 0.05]
        floor.material = "groundplane"

        spec.worldbody.add_light().pos = [0, 0, 2.5]

        def attach_arm(arm_name, pos, euler_z):
            arm_spec = mujoco.MjSpec.from_file(ARM_MODEL_PATH)
            grip_spec = mujoco.MjSpec.from_file(GRIPPER_MODEL_PATH)
            arm_spec.sites[0].attach_body(grip_spec.worldbody.first_body(), f"{arm_name}_gr-", "")

            mount = spec.worldbody.add_body()
            mount.name = f"{arm_name}_mount"
            mount.pos = pos
            mount.alt.euler = [0, 0, euler_z]

            base = mount.add_geom()
            base.name = f"{arm_name}_base"
            base.type = mujoco.mjtGeom.mjGEOM_BOX
            base.size = [0.1, 0.1, 0.15]
            base.pos = [0, 0, -0.15]
            base.rgba = [0.2, 0.2, 0.2, 1.0]

            frame = mount.add_frame()
            frame.attach_body(arm_spec.worldbody.first_body(), f"{arm_name}_", "")

        for cfg in self.arm_cfg:
            attach_arm(cfg["name"], cfg["base_pos"], cfg["euler_z"])

        for arm_idx, cfg in enumerate(self.arm_cfg):
            table = spec.worldbody.add_body()
            table.name = f"table_{cfg['name']}"
            table.pos = [cfg["table_pos"][0], cfg["table_pos"][1], 0.0]

            table_geom = table.add_geom()
            table_geom.name = f"table_{cfg['name']}_geom"
            table_geom.type = mujoco.mjtGeom.mjGEOM_BOX
            table_geom.size = [cfg["table_size"][0], cfg["table_size"][1], TABLE_Z]
            table_geom.rgba = [0.8, 0.6, 0.4, 1.0]

            obj = spec.worldbody.add_body()
            obj.name = f"obj_{cfg['name']}"
            obj.pos = cfg["obj_pos"]

            obj_joint = obj.add_freejoint()
            obj_joint.name = f"obj_{cfg['name']}_joint"

            obj_geom = obj.add_geom()
            obj_geom.name = f"obj_{cfg['name']}_geom"
            obj_geom.type = mujoco.mjtGeom.mjGEOM_BOX
            obj_geom.size = [0.025, 0.025, 0.025]
            obj_geom.rgba = cfg["obj_color"]
            obj_geom.mass = OBJECT_MASS
            obj_geom.friction = [2.0, 0.01, 0.001]

            drop = spec.worldbody.add_body()
            drop.name = f"drop_{cfg['name']}"
            drop.pos = cfg["drop_pos"]

            drop_geom = drop.add_geom()
            drop_geom.name = f"drop_{cfg['name']}_geom"
            drop_geom.type = mujoco.mjtGeom.mjGEOM_CYLINDER
            drop_geom.size = [0.055, 0.002, 0]
            drop_geom.rgba = [0.1, 0.9, 0.1, 0.5]
            drop_geom.contype = 0
            drop_geom.conaffinity = 0

        self.model = spec.compile()
        self.data = mujoco.MjData(self.model)

        self._n_arm = 6
        self._n_arms = len(self.arm_cfg)
        self._n_ctrl = self.model.nu
        self.arm_names = [cfg["name"] for cfg in self.arm_cfg]

        self._arm_qpos_adr = [
            self.model.jnt_qposadr[
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{name}_shoulder_pan_joint")
            ]
            for name in self.arm_names
        ]
        self._arm_qvel_adr = [
            self.model.jnt_dofadr[
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"{name}_shoulder_pan_joint")
            ]
            for name in self.arm_names
        ]
        self._grip_qpos_adr = [
            self.model.jnt_qposadr[
                mujoco.mj_name2id(
                    self.model,
                    mujoco.mjtObj.mjOBJ_JOINT,
                    f"{name}_{name}_gr-right_driver_joint",
                )
            ]
            for name in self.arm_names
        ]
        self._ee_sites = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, f"{name}_attachment_site")
            for name in self.arm_names
        ]
        self._obj_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, f"obj_{name}")
            for name in self.arm_names
        ]
        self._obj_geom_ids = [
            mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, f"obj_{name}_geom")
            for name in self.arm_names
        ]
        self._left_pad_geom_ids = [
            {
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, f"{name}_{name}_gr-left_pad1"),
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, f"{name}_{name}_gr-left_pad2"),
            }
            for name in self.arm_names
        ]
        self._right_pad_geom_ids = [
            {
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, f"{name}_{name}_gr-right_pad1"),
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_GEOM, f"{name}_{name}_gr-right_pad2"),
            }
            for name in self.arm_names
        ]
        self._drop_positions = [np.array(cfg["drop_pos"], dtype=np.float64) for cfg in self.arm_cfg]
        self._obj_init_pos = [np.array(cfg["obj_pos"], dtype=np.float64) for cfg in self.arm_cfg]
        self._arm_base_pos = [np.array(cfg["base_pos"], dtype=np.float64) for cfg in self.arm_cfg]
        self._arm_rot_inv = []
        for cfg in self.arm_cfg:
            theta = np.deg2rad(cfg["euler_z"])
            c, s = np.cos(theta), np.sin(theta)
            # R_z(theta)^T — transforms world vectors into the arm's local frame
            self._arm_rot_inv.append(np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]], dtype=np.float64))
        self._obj_qpos_adr = [
            self.model.jnt_qposadr[
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"obj_{name}_joint")
            ]
            for name in self.arm_names
        ]
        self._obj_qvel_adr = [
            self.model.jnt_dofadr[
                mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, f"obj_{name}_joint")
            ]
            for name in self.arm_names
        ]

        obs_dim = self._n_arms * 23
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(obs_dim,), dtype=np.float32)
        self.action_space = spaces.Box(-1.0, 1.0, shape=(self._n_ctrl,), dtype=np.float32)

        self._viewer = None
        self._phase = [0] * self._n_arms
        self._prev_dist = [None] * self._n_arms
        self._grasped = [False] * self._n_arms
        self._grasp_streak = [0] * self._n_arms
        self._episode_steps = 0
        self.max_episode_steps = 500 * self._n_arms

    def _to_local(self, world_pos, i):
        """Transform a world-space 3-vector into arm i's local frame."""
        return self._arm_rot_inv[i] @ (world_pos - self._arm_base_pos[i])

    def _reset_object_pos(self, i):
        base_pos = self._obj_init_pos[i].copy()
        if self.curriculum_mode == "none":
            return base_pos

        cfg = self.arm_cfg[i]
        table_x, table_y = cfg["table_pos"]

        if self.curriculum_mode == "grasp_focus":
            x_jitter = float(self.np_random.uniform(-0.02, 0.02))
            y_jitter = float(self.np_random.uniform(-0.025, 0.025))
            return np.array(
                [
                    table_x - 0.24 + x_jitter,
                    table_y - 0.13 + y_jitter,
                    OBJECT_Z,
                ],
                dtype=np.float64,
            )

        return np.array(
            [
                table_x,
                table_y,
                OBJECT_Z,
            ],
            dtype=np.float64,
        )

    def _object_out_of_bounds(self, i, obj):
        cfg = self.arm_cfg[i]
        table_x, table_y = cfg["table_pos"]
        table_half_x, table_half_y = cfg["table_size"]

        return (
            abs(float(obj[0]) - table_x) > table_half_x + OBJECT_RESET_X_MARGIN
            or abs(float(obj[1]) - table_y) > table_half_y + OBJECT_RESET_Y_MARGIN
            or float(obj[2]) < OBJECT_RESET_Z_MIN
            or float(obj[2]) > OBJECT_RESET_Z_MAX
        )

    def _reset_object_to_table(self, i):
        obj_qpos_adr = self._obj_qpos_adr[i]
        obj_qvel_adr = self._obj_qvel_adr[i]
        self.data.qpos[obj_qpos_adr:obj_qpos_adr + 3] = self._obj_init_pos[i]
        self.data.qpos[obj_qpos_adr + 3:obj_qpos_adr + 7] = [1, 0, 0, 0]
        self.data.qvel[obj_qvel_adr:obj_qvel_adr + 6] = 0.0
        self._phase[i] = 1 if self.curriculum_mode == "grasp_focus" else 0
        self._prev_dist[i] = None
        self._grasped[i] = False
        self._grasp_streak[i] = 0
        mujoco.mj_forward(self.model, self.data)

    def _get_obs(self):
        parts = []
        for i in range(self._n_arms):
            qpos_adr = self._arm_qpos_adr[i]
            qvel_adr = self._arm_qvel_adr[i]
            parts.append(self.data.qpos[qpos_adr:qpos_adr + self._n_arm].astype(np.float32))
            parts.append(self.data.qvel[qvel_adr:qvel_adr + self._n_arm].astype(np.float32))
            parts.append(self._to_local(self.data.site_xpos[self._ee_sites[i]], i).astype(np.float32))
            parts.append(self._to_local(self.data.xpos[self._obj_ids[i]], i).astype(np.float32))
            parts.append(self._to_local(self._drop_positions[i], i).astype(np.float32))
            parts.append(np.array([self.data.qpos[self._grip_qpos_adr[i]]], dtype=np.float32))
            parts.append(np.array([float(self._phase[i])], dtype=np.float32))
        return np.concatenate(parts)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        for i, cfg in enumerate(self.arm_cfg):
            qpos_adr = self._arm_qpos_adr[i]
            self.data.qpos[qpos_adr:qpos_adr + self._n_arm] = cfg["ready_pose"]
            ctrl_start = i * 7
            self.data.ctrl[ctrl_start:ctrl_start + self._n_arm] = cfg["ready_pose"]
            grip_idx = ctrl_start + self._n_arm
            self.data.ctrl[grip_idx] = self.model.actuator_ctrlrange[grip_idx, 0]

        for i in range(self._n_arms):
            init_pos = self._reset_object_pos(i)
            self._obj_init_pos[i] = init_pos
            obj_qpos_adr = self._obj_qpos_adr[i]
            self.data.qpos[obj_qpos_adr:obj_qpos_adr + 3] = init_pos
            self.data.qpos[obj_qpos_adr + 3:obj_qpos_adr + 7] = [1, 0, 0, 0]

        initial_phase = 1 if self.curriculum_mode == "grasp_focus" else 0
        self._phase = [initial_phase] * self._n_arms
        self._prev_dist = [None] * self._n_arms
        self._grasped = [False] * self._n_arms
        self._grasp_streak = [0] * self._n_arms
        self._episode_steps = 0

        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    def _contact_state(self, i):
        obj_geom_id = self._obj_geom_ids[i]
        left_contact = False
        right_contact = False

        for contact_idx in range(self.data.ncon):
            contact = self.data.contact[contact_idx]
            geom1 = int(contact.geom1)
            geom2 = int(contact.geom2)

            if geom1 == obj_geom_id:
                other_geom = geom2
            elif geom2 == obj_geom_id:
                other_geom = geom1
            else:
                continue

            if other_geom in self._left_pad_geom_ids[i]:
                left_contact = True
            if other_geom in self._right_pad_geom_ids[i]:
                right_contact = True

            if left_contact and right_contact:
                break

        return left_contact, right_contact

    def _is_carrying(self, grip, ee_to_obj, obj_lift, both_contacts):
        return grip > GRASP_CLOSE_THRESHOLD and (
            both_contacts or (obj_lift > CARRY_HEIGHT_THRESHOLD and ee_to_obj < 0.12)
        )

    def _arm_reward(self, i):
        ee = self.data.site_xpos[self._ee_sites[i]].copy()
        obj = self.data.xpos[self._obj_ids[i]].copy()
        drop = self._drop_positions[i]
        init_obj = self._obj_init_pos[i]
        grip = float(self.data.qpos[self._grip_qpos_adr[i]])
        qvel_adr = self._arm_qvel_adr[i]

        ee_to_obj = float(np.linalg.norm(ee - obj))
        ee_to_obj_xy = float(np.linalg.norm(ee[:2] - obj[:2]))
        ee_height_error = float(abs(ee[2] - (obj[2] + 0.03)))
        obj_to_drop_xy = float(np.linalg.norm(obj[:2] - drop[:2]))
        obj_lift = float(obj[2] - init_obj[2])
        left_contact, right_contact = self._contact_state(i)
        any_contact = left_contact or right_contact
        both_contacts = left_contact and right_contact
        carrying = self._is_carrying(grip, ee_to_obj, obj_lift, both_contacts)
        joint_vel_penalty = 0.01 * float(np.sum(np.abs(self.data.qvel[qvel_adr:qvel_adr + self._n_arm])))

        reward = -STEP_PENALTY
        terminated_arm = False
        phase = self._phase[i]

        if phase == 0:
            dist = ee_to_obj

            reward += 4.5 / (1.0 + dist * 10.0)
            reward += 7.0 / (1.0 + ee_to_obj_xy * 18.0)
            if ee_height_error < 0.06:
                reward += 6.0 * (1.0 - ee_height_error / 0.06)

            if self._prev_dist[i] is not None:
                delta = self._prev_dist[i] - dist
                reward += delta * REACH_DELTA_GAIN if delta > 0 else delta * 90.0
            self._prev_dist[i] = dist

            if ee_to_obj < 0.15:
                reward += 12.0 * (1.0 - ee_to_obj / 0.15)
            if ee_to_obj_xy < 0.07 and ee_height_error < 0.035:
                reward += 18.0
            if grip > 0.45 and ee_to_obj > 0.15:
                reward -= 2.0
            if any_contact:
                reward += 30.0
                self._phase[i] = 1
                self._prev_dist[i] = None
            elif ee_to_obj < 0.08 or (ee_to_obj_xy < 0.06 and ee_height_error < 0.03):
                self._phase[i] = 1
                self._prev_dist[i] = None
                reward += 120.0

        elif phase == 1:
            reward += 6.0 / (1.0 + ee_to_obj * 10.0)
            reward += 10.0 / (1.0 + ee_to_obj_xy * 18.0)

            if self._prev_dist[i] is not None:
                delta = self._prev_dist[i] - ee_to_obj
                reward += delta * GRASP_DELTA_GAIN if delta > 0 else delta * 80.0
            self._prev_dist[i] = ee_to_obj

            if ee_to_obj < 0.10:
                reward += 18.0 * (1.0 - ee_to_obj / 0.10)
            if ee_to_obj_xy < 0.05:
                reward += 14.0 * (1.0 - ee_to_obj_xy / 0.05)
            if any_contact:
                reward += 24.0
            if both_contacts:
                reward += 42.0
            if grip > 0.55 and not any_contact:
                reward -= 3.0
            if grip < 0.15 and ee_to_obj < 0.05:
                reward -= 4.0

            if grip > GRASP_CLOSE_THRESHOLD and any_contact:
                reward += max(0.0, obj_lift) * 1300.0
                if both_contacts:
                    reward += 36.0
                if obj_lift > GRASP_LIFT_THRESHOLD:
                    reward += 75.0
                    self._grasp_streak[i] += 1
                    reward += 12.0 * self._grasp_streak[i]
                else:
                    self._grasp_streak[i] = 0
            else:
                self._grasp_streak[i] = 0

            if self._grasp_streak[i] >= GRASP_STREAK_STEPS and carrying:
                self._grasped[i] = True
                self._phase[i] = 2
                self._prev_dist[i] = None
                reward += 900.0

        elif phase == 2:
            dist_z = abs(obj[2] - LIFT_Z)

            if self._prev_dist[i] is not None:
                delta = self._prev_dist[i] - dist_z
                reward += delta * LIFT_DELTA_GAIN if delta > 0 else delta * 100.0
            self._prev_dist[i] = dist_z

            reward += max(0.0, obj_lift) * 340.0
            if carrying:
                reward += 28.0
            else:
                reward -= 15.0

            if not carrying and obj_lift < GRASP_LIFT_THRESHOLD:
                reward -= 60.0
                self._grasped[i] = False
                self._grasp_streak[i] = 0
                self._phase[i] = 1
                self._prev_dist[i] = None
            if dist_z < 0.08:
                reward += 14.0 * (1.0 - dist_z / 0.08)

            if carrying and dist_z < 0.05 and obj_lift > CARRY_HEIGHT_THRESHOLD:
                self._phase[i] = 3
                self._prev_dist[i] = None
                reward += 320.0

        elif phase == 3:
            if self._prev_dist[i] is not None:
                delta = self._prev_dist[i] - obj_to_drop_xy
                reward += delta * CARRY_DELTA_GAIN if delta > 0 else delta * 70.0
            self._prev_dist[i] = obj_to_drop_xy

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
                self._grasped[i] = False
                self._grasp_streak[i] = 0
                self._phase[i] = 1
                self._prev_dist[i] = None

            if obj_to_drop_xy < 0.08 and grip < 0.1 and obj[2] < init_obj[2] + 0.015:
                self._grasped[i] = False
                reward += 1800.0
                terminated_arm = True

        reward -= joint_vel_penalty
        return reward / REWARD_SCALE, terminated_arm, phase, carrying, any_contact, both_contacts

    def step(self, action):
        self._episode_steps += 1

        for i in range(self._n_arms):
            start = i * 7
            arm_action = np.asarray(action[start:start + self._n_arm], dtype=np.float64)
            arm_target = self.arm_cfg[i]["ready_pose"] + arm_action * ARM_ACTION_SCALE
            arm_ctrlrange = self.model.actuator_ctrlrange[start:start + self._n_arm]
            self.data.ctrl[start:start + self._n_arm] = np.clip(
                arm_target,
                arm_ctrlrange[:, 0],
                arm_ctrlrange[:, 1],
            )
            grip_idx = start + self._n_arm
            if grip_idx < self.model.nu:
                grip_low, grip_high = self.model.actuator_ctrlrange[grip_idx]
                grip_command = (float(action[grip_idx]) + 1.0) / 2.0
                self.data.ctrl[grip_idx] = grip_low + grip_command * (grip_high - grip_low)

        for _ in range(5):
            mujoco.mj_step(self.model, self.data)

        total_reward = 0.0
        info = {}
        all_done = True
        phase_counts = {phase_idx: 0 for phase_idx in range(4)}
        carrying_count = 0
        any_contact_count = 0
        both_contacts_count = 0
        object_reset_count = 0
        done_count = 0
        ee_to_obj_distances = []
        obj_heights = []
        obj_to_drop_distances = []
        arm_rewards = []

        for i, name in enumerate(self.arm_names):
            reward, arm_done, phase, carrying, any_contact, both_contacts = self._arm_reward(i)
            total_reward += reward
            if not arm_done:
                all_done = False

            obj = self.data.xpos[self._obj_ids[i]].copy()
            ee = self.data.site_xpos[self._ee_sites[i]].copy()
            qpos_adr = self._arm_qpos_adr[i]
            ee_to_obj = float(np.linalg.norm(ee - obj))
            object_reset = self._object_out_of_bounds(i, obj)
            if object_reset:
                total_reward -= OBJECT_RESET_PENALTY
                reward -= OBJECT_RESET_PENALTY
                self._reset_object_to_table(i)
                obj = self.data.xpos[self._obj_ids[i]].copy()
                phase = self._phase[i]
                carrying = False
                any_contact = False
                both_contacts = False
                ee_to_obj = float(np.linalg.norm(ee - obj))
            phase_counts[int(phase)] += 1
            carrying_count += int(carrying)
            any_contact_count += int(any_contact)
            both_contacts_count += int(both_contacts)
            object_reset_count += int(object_reset)
            done_count += int(arm_done)
            ee_to_obj_distances.append(ee_to_obj)
            obj_heights.append(float(obj[2]))
            obj_to_drop_distances.append(float(np.linalg.norm(obj[:2] - self._drop_positions[i][:2])))
            arm_rewards.append(float(reward))
            info[f"{name}_phase"] = phase
            info[f"{name}_done"] = arm_done
            info[f"{name}_reward"] = float(reward)
            info[f"{name}_object_reset"] = object_reset
            info[f"{name}_carrying"] = carrying
            info[f"{name}_any_contact"] = any_contact
            info[f"{name}_both_contacts"] = both_contacts
            info[f"{name}_grasp_streak"] = self._grasp_streak[i]
            info[f"{name}_ee_pos"] = ee.astype(float).round(4).tolist()
            info[f"{name}_obj_pos"] = obj.astype(float).round(4).tolist()
            info[f"{name}_drop_pos"] = self._drop_positions[i].astype(float).round(4).tolist()
            info[f"{name}_gripper_qpos"] = float(self.data.qpos[self._grip_qpos_adr[i]])
            info[f"{name}_arm_qpos"] = self.data.qpos[qpos_adr:qpos_adr + self._n_arm].astype(float).round(4).tolist()
            info[f"{name}_obj_height"] = float(obj[2])
            info[f"{name}_ee_to_obj"] = ee_to_obj
            info[f"{name}_obj_to_drop"] = obj_to_drop_distances[-1]

        arm_count = max(self._n_arms, 1)
        info["scene_summary"] = {
            "phase_counts": {str(phase_idx): count for phase_idx, count in phase_counts.items()},
            "phase_fractions": {str(phase_idx): count / arm_count for phase_idx, count in phase_counts.items()},
            "max_phase": max((phase_idx for phase_idx, count in phase_counts.items() if count > 0), default=0),
            "carrying_count": carrying_count,
            "any_contact_count": any_contact_count,
            "both_contacts_count": both_contacts_count,
            "object_reset_count": object_reset_count,
            "done_count": done_count,
            "mean_arm_reward": float(np.mean(arm_rewards)) if arm_rewards else 0.0,
            "mean_ee_to_obj": float(np.mean(ee_to_obj_distances)) if ee_to_obj_distances else 0.0,
            "min_ee_to_obj": float(np.min(ee_to_obj_distances)) if ee_to_obj_distances else 0.0,
            "mean_obj_height": float(np.mean(obj_heights)) if obj_heights else 0.0,
            "max_obj_height": float(np.max(obj_heights)) if obj_heights else 0.0,
            "mean_obj_to_drop": float(np.mean(obj_to_drop_distances)) if obj_to_drop_distances else 0.0,
            "min_obj_to_drop": float(np.min(obj_to_drop_distances)) if obj_to_drop_distances else 0.0,
        }

        terminated = all_done
        truncated = self._episode_steps >= self.max_episode_steps

        if self.render_mode == "human":
            self.render()

        return self._get_obs(), total_reward, terminated, truncated, info

    def render(self):
        if self.render_mode == "human":
            if self._viewer is None:
                self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self._viewer.sync()

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
