import numpy as np
import gymnasium as gym
from gymnasium import spaces
from stable_baselines3.common.vec_env import VecEnv

from envs.ur_dual_arm_env import URDualArmEnv


LOCAL_OBS_DIM = 23
LOCAL_ACTION_DIM = 7


class SharedArmPickPlaceEnv(gym.Env):
    """
    Train one reusable arm policy from a local per-arm view.
    The wrapped scene can contain many arms, but each episode trains the policy
    on one selected arm's 23-dim observation and 7-dim action.
    """

    metadata = URDualArmEnv.metadata

    def __init__(
        self,
        render_mode=None,
        arm_count=8,
        curriculum_mode="easy_grasp",
        arm_index=None,
        max_episode_steps=500,
    ):
        self.env = URDualArmEnv(
            render_mode=render_mode,
            arm_count=arm_count,
            curriculum_mode=curriculum_mode,
        )
        self.arm_index = arm_index
        self.max_episode_steps = max_episode_steps
        self._selected_arm = 0
        self._episode_steps = 0

        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(LOCAL_OBS_DIM,), dtype=np.float32)
        self.action_space = spaces.Box(-1.0, 1.0, shape=(LOCAL_ACTION_DIM,), dtype=np.float32)

    @property
    def arm_names(self):
        return self.env.arm_names

    def _select_arm(self):
        if self.arm_index is not None:
            return int(self.arm_index)
        return int(self.np_random.integers(0, len(self.env.arm_names)))

    def _local_obs(self, obs):
        start = self._selected_arm * LOCAL_OBS_DIM
        return obs[start:start + LOCAL_OBS_DIM].astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        obs, info = self.env.reset(seed=seed, options=options)
        self._selected_arm = self._select_arm()
        self._episode_steps = 0
        info = dict(info)
        info["selected_arm"] = self.env.arm_names[self._selected_arm]
        info["selected_arm_index"] = self._selected_arm
        return self._local_obs(obs), info

    def step(self, action):
        self._episode_steps += 1

        full_action = np.zeros(self.env.action_space.shape, dtype=np.float32)
        start = self._selected_arm * LOCAL_ACTION_DIM
        full_action[start:start + LOCAL_ACTION_DIM] = np.asarray(action, dtype=np.float32)

        obs, total_reward, terminated, truncated, info = self.env.step(full_action)

        arm_name = self.env.arm_names[self._selected_arm]
        reward = float(info.get(f"{arm_name}_reward", total_reward))
        arm_done = bool(info.get(f"{arm_name}_done", terminated))
        time_limit = self._episode_steps >= self.max_episode_steps

        info = dict(info)
        info["selected_arm"] = arm_name
        info["selected_arm_index"] = self._selected_arm
        info["selected_arm_reward"] = reward

        return self._local_obs(obs), reward, arm_done, bool(truncated or time_limit), info

    def render(self):
        return self.env.render()

    def close(self):
        self.env.close()


class SharedArmBatchVecEnv(VecEnv):
    """
    VecEnv that turns each arm in each MuJoCo scene into a shared-policy sample.
    A single 8-arm scene becomes an 8-env vector from SAC's perspective.
    """

    def __init__(self, arm_count=8, scene_count=1, curriculum_mode="easy_grasp", render_mode=None):
        self.arm_count = arm_count
        self.scene_count = scene_count
        self.curriculum_mode = curriculum_mode
        self.envs = [
            URDualArmEnv(
                render_mode=render_mode,
                arm_count=arm_count,
                curriculum_mode=curriculum_mode,
            )
            for _ in range(scene_count)
        ]
        self.actions = None
        self._obs = [None for _ in range(scene_count)]

        observation_space = spaces.Box(-np.inf, np.inf, shape=(LOCAL_OBS_DIM,), dtype=np.float32)
        action_space = spaces.Box(-1.0, 1.0, shape=(LOCAL_ACTION_DIM,), dtype=np.float32)
        super().__init__(scene_count * arm_count, observation_space, action_space)

    def _scene_arm(self, vec_index):
        return divmod(vec_index, self.arm_count)

    def _local_obs_from_scene(self, scene_obs, arm_index):
        start = arm_index * LOCAL_OBS_DIM
        return scene_obs[start:start + LOCAL_OBS_DIM].astype(np.float32)

    def _batch_obs(self):
        obs = np.zeros((self.num_envs, LOCAL_OBS_DIM), dtype=np.float32)
        for scene_index, scene_obs in enumerate(self._obs):
            for arm_index in range(self.arm_count):
                vec_index = scene_index * self.arm_count + arm_index
                obs[vec_index] = self._local_obs_from_scene(scene_obs, arm_index)
        return obs

    def reset(self):
        for scene_index, env in enumerate(self.envs):
            seed = self._seeds[scene_index] if scene_index < len(self._seeds) else None
            options = self._options[scene_index] if scene_index < len(self._options) else None
            self._obs[scene_index], reset_info = env.reset(seed=seed, options=options)
            for arm_index, arm_name in enumerate(env.arm_names):
                vec_index = scene_index * self.arm_count + arm_index
                self.reset_infos[vec_index] = {
                    "scene_index": scene_index,
                    "arm_index": arm_index,
                    "arm_name": arm_name,
                    **reset_info,
                }
        self._reset_seeds()
        self._reset_options()
        return self._batch_obs()

    def step_async(self, actions):
        self.actions = np.asarray(actions, dtype=np.float32)

    def step_wait(self):
        if self.actions is None:
            raise RuntimeError("step_async() must be called before step_wait().")

        batch_obs = np.zeros((self.num_envs, LOCAL_OBS_DIM), dtype=np.float32)
        rewards = np.zeros((self.num_envs,), dtype=np.float32)
        dones = np.zeros((self.num_envs,), dtype=bool)
        infos = [{} for _ in range(self.num_envs)]

        for scene_index, env in enumerate(self.envs):
            full_action = np.zeros(env.action_space.shape, dtype=np.float32)
            for arm_index in range(self.arm_count):
                vec_index = scene_index * self.arm_count + arm_index
                start = arm_index * LOCAL_ACTION_DIM
                full_action[start:start + LOCAL_ACTION_DIM] = self.actions[vec_index]

            scene_obs, scene_reward, scene_terminated, scene_truncated, scene_info = env.step(full_action)
            scene_done = bool(scene_terminated or scene_truncated)
            arm_dones = []

            for arm_index, arm_name in enumerate(env.arm_names):
                arm_dones.append(bool(scene_info.get(f"{arm_name}_done", False)))

            reset_scene = scene_done or any(arm_dones)
            terminal_obs = scene_obs

            if reset_scene:
                reset_obs, reset_info = env.reset()
                self._obs[scene_index] = reset_obs
            else:
                reset_info = {}
                self._obs[scene_index] = scene_obs

            for arm_index, arm_name in enumerate(env.arm_names):
                vec_index = scene_index * self.arm_count + arm_index
                obs_source = self._obs[scene_index]
                batch_obs[vec_index] = self._local_obs_from_scene(obs_source, arm_index)
                rewards[vec_index] = float(scene_info.get(f"{arm_name}_reward", scene_reward / self.arm_count))
                dones[vec_index] = reset_scene
                infos[vec_index] = {
                    "scene_index": scene_index,
                    "arm_index": arm_index,
                    "arm_name": arm_name,
                    "TimeLimit.truncated": bool(scene_truncated and not scene_terminated),
                    "terminal_observation": self._local_obs_from_scene(terminal_obs, arm_index) if reset_scene else None,
                    **reset_info,
                    **scene_info,
                }

        self.actions = None
        return batch_obs, rewards, dones, infos

    def close(self):
        for env in self.envs:
            env.close()

    def get_attr(self, attr_name, indices=None):
        return [getattr(self.envs[scene_index], attr_name) for scene_index, _ in self._iter_indices(indices)]

    def set_attr(self, attr_name, value, indices=None):
        for scene_index, _ in self._iter_indices(indices, unique_scenes=True):
            setattr(self.envs[scene_index], attr_name, value)

    def env_method(self, method_name, *method_args, indices=None, **method_kwargs):
        return [
            getattr(self.envs[scene_index], method_name)(*method_args, **method_kwargs)
            for scene_index, _ in self._iter_indices(indices)
        ]

    def env_is_wrapped(self, wrapper_class, indices=None):
        return [False for _ in self._iter_indices(indices)]

    def _iter_indices(self, indices=None, unique_scenes=False):
        if indices is None:
            raw_indices = range(self.num_envs)
        elif isinstance(indices, int):
            raw_indices = [indices]
        else:
            raw_indices = indices

        seen_scenes = set()
        for vec_index in raw_indices:
            scene_index, arm_index = self._scene_arm(int(vec_index))
            if unique_scenes and scene_index in seen_scenes:
                continue
            seen_scenes.add(scene_index)
            yield scene_index, arm_index

    def render(self, mode=None):
        return self.envs[0].render()
