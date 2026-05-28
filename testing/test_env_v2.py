#!/usr/bin/env python3
"""
Quick sanity check for UR3PickPlaceEnvV2.
Verifies: reward is ~0 when standing still, info["success"] is set,
and the gripper-closure reward fires correctly.
"""
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ur_rl_training"))

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"
failures = []


def check(name, cond, detail=""):
    if cond:
        print(f"  {PASS}  {name}")
    else:
        print(f"  {FAIL}  {name}  {detail}")
        failures.append(name)


from envs.ur3_pick_place_env_v2 import UR3PickPlaceEnvV2, REWARD_SCALE

print("\nUR3PickPlaceEnvV2 sanity checks\n" + "─"*40)

env = UR3PickPlaceEnvV2(curriculum_mode="grasp_focus", domain_randomisation=False)
obs, _ = env.reset(seed=42)

# ── 1. Observation shape ──────────────────────────────────────────────────────
check("obs shape is (23,)", obs.shape == (23,), str(obs.shape))
check("action space (7,)", env.action_space.shape == (7,), str(env.action_space.shape))

# ── 2. Standing still gives ~0 reward at 0.20 m ──────────────────────────────
# Manually place the EE far from the object and check reward
# We can't move the EE directly, but we can run a no-op step and check
zero_action = np.zeros(7)
_, reward_noop, _, _, _ = env.step(zero_action)
# At 0.15-0.22 m distance in phase 1, v2 reward should be small (< 0.05)
check("no-op reward < 0.05 (no local optimum)", abs(reward_noop) < 0.05,
      f"got {reward_noop:.4f}")

# ── 3. Episode resets cleanly ─────────────────────────────────────────────────
obs2, info = env.reset(seed=100)
check("reset returns (23,) obs", obs2.shape == (23,))
check("reset info is dict",      isinstance(info, dict))

# ── 4. Phase starts at 1 in grasp_focus ──────────────────────────────────────
check("phase=1 at reset (grasp_focus)", env._phase == 1)

# ── 5. info dict has 'success' and 'phase' keys ──────────────────────────────
_, _, _, _, info_step = env.step(zero_action)
check("info has 'success' key", "success" in info_step, str(info_step))
check("info has 'phase' key",   "phase"   in info_step)
check("success=False on normal step", info_step["success"] == False)

# ── 6. Gripper closure reward fires when close ───────────────────────────────
# Check the reward function directly with synthetic values
from envs.ur3_pick_place_env_v2 import GRASP_CLOSE_THRESHOLD
env_test = UR3PickPlaceEnvV2(domain_randomisation=False)
env_test.reset(seed=0)
env_test._phase = 1
env_test._prev_dist = 0.06  # pretend we were 6 cm away last step
# Set gripper control to half-closed
env_test.data.ctrl[6] = env_test.model.actuator_ctrlrange[6, 1] * 0.5
env_test.data.qpos[env_test._grip_qpos] = 0.4  # gripper at 0.4 rad (>0.28 threshold)
# Move the object under the EE site
ee_pos = env_test.data.site_xpos[env_test._ee_site].copy()
s = env_test._obj_qpos_start
env_test.data.qpos[s:s+3] = [ee_pos[0], ee_pos[1], ee_pos[2] - 0.05]
import mujoco
mujoco.mj_forward(env_test.model, env_test.data)
reward_close, _ = env_test._reward()
check("reward > 0 when close + gripping", reward_close > 0,
      f"got {reward_close:.4f}")

# ── 7. Episode shorter (≤ 8 s sim time) ──────────────────────────────────────
from envs.ur3_pick_place_env_v2 import MAX_SIM_TIME
check("MAX_SIM_TIME <= 8.0", MAX_SIM_TIME <= 8.0, f"got {MAX_SIM_TIME}")

# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'─'*40}")
total = 9
passed = total - len(failures)
print(f"Results: {passed}/{total} passed")
if failures:
    print(f"Failed: {failures}")
    sys.exit(1)
else:
    print("All checks passed.")
    sys.exit(0)
