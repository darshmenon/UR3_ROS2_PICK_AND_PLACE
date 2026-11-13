"""Render a trained DAgger or flow policy (scripts/dagger.py, scripts/flow_policy.py) in the MuJoCo environment to a GIF, headless.

Run from ur_rl_training/:
    MUJOCO_GL=osmesa python3 scripts/render_policy.py --policy ~/ur3_rl_demos/dagger.pt --out ../assets/gifs/rl_dagger.gif
"""
import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("MUJOCO_GL", "osmesa")
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import imageio.v2 as imageio  # noqa: E402
import mujoco  # noqa: E402
import numpy as np  # noqa: E402

from eval_policy import load_actor  # noqa: E402
from envs.ur3_pick_place_env_v2 import UR3PickPlaceEnvV2  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", default=str(Path.home() / "ur3_rl_demos" / "dagger.pt"))
    ap.add_argument("--out", default=str(REPO_ROOT.parent / "assets" / "gifs" / "rl_dagger.gif"))
    ap.add_argument("--seed", type=int, default=5000)
    ap.add_argument("--tries", type=int, default=6, help="episodes to try; the first success is saved")
    ap.add_argument("--max-steps", type=int, default=800)
    ap.add_argument("--every", type=int, default=6, help="steps per GIF frame")
    ap.add_argument("--size", type=int, nargs=2, default=(480, 360))
    args = ap.parse_args()

    env = UR3PickPlaceEnvV2(curriculum_mode="grasp_focus", domain_randomisation=False)
    act = load_actor(args.policy, env.observation_space.shape[0], env.action_space.shape[0])
    env.model.vis.headlight.ambient[:] = 0.5      # the scene has no lights of its own: the render is black without this
    env.model.vis.headlight.diffuse[:] = 0.9
    renderer = mujoco.Renderer(env.model, height=args.size[1], width=args.size[0])
    cam = mujoco.MjvCamera()
    cam.lookat[:] = [0.3, 0.05, 0.15]
    cam.distance, cam.azimuth, cam.elevation = 0.95, 140, -28

    for ep in range(args.tries):
        obs, _ = env.reset(seed=args.seed + ep)
        act.reset()
        frames, ok = [], False
        for t in range(args.max_steps):
            obs, _, term, trunc, info = env.step(act(obs))
            if t % args.every == 0:
                renderer.update_scene(env.data, camera=cam)
                frames.append(renderer.render())
            if term or trunc:
                ok = bool(term and info.get("success"))
                break
        print(f"episode {ep}: {'success' if ok else 'fail'} in {t + 1} steps, {len(frames)} frames", flush=True)
        if ok:
            imageio.mimsave(args.out, frames, duration=0.06, loop=0)
            imageio.imwrite(str(Path(args.out).with_suffix(".png")), frames[-1])
            print("saved", args.out)
            return
    print("no successful episode to save")


if __name__ == "__main__":
    main()
