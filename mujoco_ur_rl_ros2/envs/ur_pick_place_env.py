import numpy as np
import mujoco
import mujoco.viewer
import gymnasium as gym
from gymnasium import spaces


class URPickPlaceEnv(gym.Env):
    """
    UR5e pick-and-place task:
    - Pick a red box from the table
    - Place it at a green target zone
    """

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(self, render_mode=None):
        self.render_mode = render_mode

        arm = mujoco.MjSpec.from_file(
            "/home/asimov/mujoco_menagerie/universal_robots_ur5e/ur5e.xml"
        )
        gripper_spec = mujoco.MjSpec.from_file(
            "/home/asimov/mujoco_menagerie/robotiq_2f85/2f85.xml"
        )
        arm.sites[0].attach_body(gripper_spec.worldbody.first_body(), "gripper-", "")

        # Table
        table = arm.worldbody.add_body()
        table.name = "table"
        table.pos = [0.5, 0.0, 0.0]
        tg = table.add_geom()
        tg.name = "table_geom"
        tg.type = mujoco.mjtGeom.mjGEOM_BOX
        tg.size = [0.3, 0.3, 0.02]
        tg.rgba = [0.8, 0.6, 0.4, 1]

        # Object to pick (red box)
        obj = arm.worldbody.add_body()
        obj.name = "object"
        obj.pos = [0.45, 0.0, 0.045]
        fj = obj.add_freejoint()
        fj.name = "object_joint"
        og = obj.add_geom()
        og.name = "object_geom"
        og.type = mujoco.mjtGeom.mjGEOM_BOX
        og.size = [0.025, 0.025, 0.025]
        og.rgba = [0.9, 0.1, 0.1, 1]
        og.friction = [1.5, 0.005, 0.0001]
        og.mass = 0.1

        # Target zone marker (green, no collision)
        target = arm.worldbody.add_body()
        target.name = "target_zone"
        target.pos = [0.45, 0.2, 0.022]
        tzone = target.add_geom()
        tzone.name = "target_zone_geom"
        tzone.type = mujoco.mjtGeom.mjGEOM_CYLINDER
        tzone.size = [0.04, 0.002, 0]
        tzone.rgba = [0.1, 0.9, 0.1, 0.4]
        tzone.contype = 0
        tzone.conaffinity = 0

        self.model = arm.compile()
        self.data = mujoco.MjData(self.model)

        self._n_arm_joints = 6
        self._n_gripper_joints = 1
        self._n_ctrl = self._n_arm_joints + self._n_gripper_joints

        # IDs cached after compile
        self._ee_site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "attachment_site")
        self._obj_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "object")
        self._target_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "target_zone")

        self._target_pos = np.array([0.45, 0.2, 0.025])

        # obs: qpos(6) + qvel(6) + ee_pos(3) + obj_pos(3) + obj_vel(3) + target_pos(3) + gripper(1)
        obs_dim = 6 + 6 + 3 + 3 + 3 + 3 + 1
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(obs_dim,), dtype=np.float32)

        # actions: 6 arm joints + 1 gripper (all -1 to 1)
        self.action_space = spaces.Box(-1.0, 1.0, shape=(self._n_ctrl,), dtype=np.float32)

        self._viewer = None
        self._phase = "reach"  # reach -> grasp -> lift -> place

    def _get_ee_pos(self):
        return self.data.site_xpos[self._ee_site_id].copy()

    def _get_obj_pos(self):
        return self.data.xpos[self._obj_body_id].copy()

    def _get_obs(self):
        qpos = self.data.qpos[:self._n_arm_joints].astype(np.float32)
        qvel = self.data.qvel[:self._n_arm_joints].astype(np.float32)
        ee_pos = self._get_ee_pos().astype(np.float32)
        obj_pos = self._get_obj_pos().astype(np.float32)
        obj_vel = self.data.qvel[7:10].astype(np.float32) if self.model.nv > 10 else np.zeros(3, np.float32)
        target = self._target_pos.astype(np.float32)
        gripper = np.array([self.data.qpos[self._n_arm_joints]], dtype=np.float32)
        return np.concatenate([qpos, qvel, ee_pos, obj_pos, obj_vel, target, gripper])

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        self._phase = "reach"

        # Randomize object position on table
        ox = self.np_random.uniform(0.35, 0.55)
        oy = self.np_random.uniform(-0.15, 0.15)
        obj_qpos_start = self._n_arm_joints + self._n_gripper_joints
        self.data.qpos[obj_qpos_start:obj_qpos_start + 3] = [ox, oy, 0.045]
        self.data.qpos[obj_qpos_start + 3:obj_qpos_start + 7] = [1, 0, 0, 0]

        # Randomize target zone
        tx = self.np_random.uniform(0.35, 0.55)
        ty = self.np_random.uniform(0.15, 0.25)
        self._target_pos = np.array([tx, ty, 0.025])
        self.model.body_pos[self._target_body_id] = self._target_pos

        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    def step(self, action):
        arm_action = action[:self._n_arm_joints] * 0.5
        gripper_action = action[self._n_arm_joints]

        self.data.ctrl[:self._n_arm_joints] = arm_action
        # Map gripper: -1=open, +1=close
        gripper_ctrl_idx = self._n_arm_joints
        if gripper_ctrl_idx < self.model.nu:
            self.data.ctrl[gripper_ctrl_idx] = (gripper_action + 1) / 2 * 0.8

        for _ in range(5):
            mujoco.mj_step(self.model, self.data)

        ee_pos = self._get_ee_pos()
        obj_pos = self._get_obj_pos()

        dist_ee_obj = np.linalg.norm(ee_pos - obj_pos)
        dist_obj_target = np.linalg.norm(obj_pos[:2] - self._target_pos[:2])
        obj_height = obj_pos[2]

        # Shaped reward
        reward = 0.0
        reward -= 0.5 * dist_ee_obj          # reach object
        reward -= 1.0 * dist_obj_target      # move object to target
        reward += 0.5 * max(0, obj_height - 0.05)  # lift bonus

        if dist_obj_target < 0.05 and obj_height < 0.05:
            reward += 10.0  # placed!

        terminated = bool(dist_obj_target < 0.04 and obj_height < 0.05)
        truncated = bool(self.data.time > 15.0)

        if self.render_mode == "human":
            self.render()

        return self._get_obs(), reward, terminated, truncated, {
            "dist_ee_obj": dist_ee_obj,
            "dist_obj_target": dist_obj_target,
            "obj_height": obj_height,
        }

    def render(self):
        if self.render_mode == "human":
            if self._viewer is None:
                self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self._viewer.sync()

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
