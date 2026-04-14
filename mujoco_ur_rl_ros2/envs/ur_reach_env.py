import numpy as np
import mujoco
import mujoco.viewer
import gymnasium as gym
from gymnasium import spaces


class URReachEnv(gym.Env):
    """UR5e reach task: move end-effector to a target position."""

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 50}

    def __init__(self, render_mode=None):
        self.render_mode = render_mode

        self._arm = mujoco.MjSpec.from_file(
            "/home/asimov/mujoco_menagerie/universal_robots_ur5e/ur5e.xml"
        )
        self._gripper_spec = mujoco.MjSpec.from_file(
            "/home/asimov/mujoco_menagerie/robotiq_2f85/2f85.xml"
        )
        site = self._arm.sites[0]
        site.attach_body(self._gripper_spec.worldbody.first_body(), "gripper-", "")

        # Add target marker
        target = self._arm.worldbody.add_body()
        target.name = "target"
        target.pos = [0.4, 0.0, 0.4]
        tgeom = target.add_geom()
        tgeom.name = "target_geom"
        tgeom.type = mujoco.mjtGeom.mjGEOM_SPHERE
        tgeom.size = [0.02, 0, 0]
        tgeom.rgba = [1, 0, 0, 0.5]
        tgeom.contype = 0
        tgeom.conaffinity = 0

        self.model = self._arm.compile()
        self.data = mujoco.MjData(self.model)

        self._n_joints = 6  # UR5e joints only
        self._dt = self.model.opt.timestep * 5  # 5 sim steps per action

        # Joint position + velocity obs + target pos
        obs_dim = self._n_joints * 2 + 3
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
        )
        # Normalized joint velocity commands
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(self._n_joints,), dtype=np.float32
        )

        self._target_pos = np.array([0.4, 0.0, 0.4])
        self._viewer = None

    def _get_ee_pos(self):
        site_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_SITE, "attachment_site")
        return self.data.site_xpos[site_id].copy()

    def _get_obs(self):
        qpos = self.data.qpos[:self._n_joints].astype(np.float32)
        qvel = self.data.qvel[:self._n_joints].astype(np.float32)
        target = self._target_pos.astype(np.float32)
        return np.concatenate([qpos, qvel, target])

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)

        # Randomize target within reachable workspace
        r = self.np_random.uniform(0.2, 0.55)
        theta = self.np_random.uniform(-np.pi / 2, np.pi / 2)
        phi = self.np_random.uniform(0.1, np.pi / 2)
        self._target_pos = np.array([
            r * np.sin(phi) * np.cos(theta),
            r * np.sin(phi) * np.sin(theta),
            r * np.cos(phi),
        ])
        target_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "target")
        self.model.body_pos[target_id] = self._target_pos

        mujoco.mj_forward(self.model, self.data)
        return self._get_obs(), {}

    def step(self, action):
        self.data.ctrl[:self._n_joints] = action * 0.5  # scale to rad/s

        for _ in range(5):
            mujoco.mj_step(self.model, self.data)

        ee_pos = self._get_ee_pos()
        dist = np.linalg.norm(ee_pos - self._target_pos)

        reward = -dist
        if dist < 0.05:
            reward += 1.0  # bonus for reaching

        terminated = bool(dist < 0.02)
        truncated = bool(self.data.time > 10.0)

        if self.render_mode == "human":
            self.render()

        return self._get_obs(), reward, terminated, truncated, {"dist": dist}

    def render(self):
        if self.render_mode == "human":
            if self._viewer is None:
                self._viewer = mujoco.viewer.launch_passive(self.model, self.data)
            self._viewer.sync()

    def close(self):
        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None
