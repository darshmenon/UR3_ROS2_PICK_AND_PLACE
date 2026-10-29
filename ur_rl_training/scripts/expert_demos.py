"""Scripted pick-and-place expert for the MuJoCo environment, to give RL a good start (CPU only).

A state machine drives the end effector with damped-least-squares Jacobian IK and turns the result into the
environment's own action (joint deltas + gripper delta):

    above the object -> descend -> close -> lift -> over the drop spot -> lower -> open

Successful episodes are saved as transitions (obs, action, reward, next_obs, done); train_v2.py --demos uses them
to pretrain the SAC actor and to fill the replay buffer.

Run from ur_rl_training/:
    python3 scripts/expert_demos.py --episodes 100 --out ~/ur3_rl_demos/expert.npz
"""
import argparse
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import mujoco  # noqa: E402
import numpy as np  # noqa: E402

from envs.ur3_pick_place_env_v2 import N_ARM, UR3PickPlaceEnvV2  # noqa: E402

# The tracked point (attachment_site, the wrist flange) sits ~0.103 m above the finger pads, so these are heights of
# the FLANGE: with GRASP_DZ the pads straddle the object. (The env's own reward asks for the flange 0.03 m above the
# object, which the gripper geometry cannot reach: the pads are on the table at 0.157 m.)
PAD_OFFSET = 0.103
ABOVE = 0.19        # hover height above the object centre (m)
GRASP_DZ = 0.118    # = flange 0.163 m: just above the 0.157 m floor where the pads touch the table
LIFT_DZ = 0.27      # absolute flange height while carrying
DAMPING = 0.05
MAX_DQ = 0.08       # rad per step, <= the env's 0.1 rad action scale


class Expert:
    def __init__(self, env: UR3PickPlaceEnvV2):
        self.env = env
        self.jacp = np.zeros((3, env.model.nv))
        self.jacr = np.zeros((3, env.model.nv))
        self.phase = "above"
        self.t_phase = 0
        self.hold_xy = None

    def _goto(self, target, tol=0.012, gain=3.0):
        """Joint-delta action moving the end effector toward `target`; second value says whether it is there."""
        env = self.env
        ee = env.data.site_xpos[env._ee_site].copy()
        err = target - ee
        mujoco.mj_jacSite(env.model, env.data, self.jacp, self.jacr, env._ee_site)
        J = self.jacp[:, :N_ARM]
        dq = J.T @ np.linalg.solve(J @ J.T + DAMPING ** 2 * np.eye(3), gain * err)
        peak = np.abs(dq).max()
        if peak > MAX_DQ:
            dq *= MAX_DQ / peak
        return dq / 0.1, float(np.linalg.norm(err)) < tol

    def act(self):
        env = self.env
        obj = env.data.xpos[env._obj_body].copy()
        drop = env._drop_pos.copy()
        grip = float(env.data.qpos[env._grip_qpos])
        a = np.zeros(N_ARM + 1)
        self.t_phase += 1

        def move(target, nxt, tol=0.012, grip_cmd=-1.0):
            dq, done = self._goto(target, tol)
            a[:N_ARM] = dq
            a[N_ARM] = grip_cmd
            if done:
                self.phase, self.t_phase = nxt, 0

        if self.phase == "above":
            move(obj + [0, 0, ABOVE], "descend", tol=0.02)
        elif self.phase == "descend":
            move(obj + [0, 0, GRASP_DZ], "close", tol=0.015)
        elif self.phase == "close":
            a[N_ARM] = 1.0
            if grip > 0.42 or self.t_phase > 40:
                self.phase, self.t_phase = "lift", 0
        elif self.phase == "lift":                    # straight up: never chase the held object's x/y
            ee = env.data.site_xpos[env._ee_site]
            if self.hold_xy is None:
                self.hold_xy = ee[:2].copy()
            move(np.array([self.hold_xy[0], self.hold_xy[1], LIFT_DZ]), "carry", tol=0.02, grip_cmd=1.0)
        elif self.phase in ("carry", "lower"):        # put the OBJECT (not the hand) over the drop spot
            ee = env.data.site_xpos[env._ee_site]
            xy = drop[:2] + (ee[:2] - obj[:2])
            z = LIFT_DZ if self.phase == "carry" else drop[2] + 0.14
            move(np.array([xy[0], xy[1], z]), "lower" if self.phase == "carry" else "open", tol=0.02, grip_cmd=1.0)
        else:  # open: release, then stay put
            a[N_ARM] = -1.0
        return np.clip(a, -1.0, 1.0).astype(np.float32)


def collect(episodes, seed, max_steps, curriculum):
    env = UR3PickPlaceEnvV2(curriculum_mode=curriculum, domain_randomisation=False)
    data = {k: [] for k in ("obs", "act", "rew", "next_obs", "done")}
    ok = 0
    for ep in range(episodes):
        obs, _ = env.reset(seed=seed + ep)
        ex = Expert(env)
        traj, success = [], False
        for _ in range(max_steps):
            a = ex.act()
            nobs, r, term, trunc, info = env.step(a)
            traj.append((obs, a, r, nobs, float(term)))
            obs = nobs
            if term or trunc:
                success = bool(term and info.get("success"))
                break
        ok += success
        if success:
            for o, a, r, n, d in traj:
                for k, v in zip(("obs", "act", "rew", "next_obs", "done"), (o, a, r, n, d)):
                    data[k].append(v)
        print(f"episode {ep + 1}/{episodes}: {'success' if success else 'fail'} in {len(traj)} steps "
              f"(phase {ex.phase}); {ok} kept", flush=True)
    return {k: np.asarray(v, dtype=np.float32) for k, v in data.items()}, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-steps", type=int, default=800)
    ap.add_argument("--curriculum", default="grasp_focus", choices=["none", "grasp_focus"])
    ap.add_argument("--out", default=str(Path.home() / "ur3_rl_demos" / "expert.npz"))
    args = ap.parse_args()
    t0 = time.time()
    data, ok = collect(args.episodes, args.seed, args.max_steps, args.curriculum)
    print(f"{ok}/{args.episodes} successful episodes, {len(data['obs'])} transitions, {time.time() - t0:.0f} s")
    if ok:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(args.out, **data)
        print("saved", args.out)


if __name__ == "__main__":
    main()
