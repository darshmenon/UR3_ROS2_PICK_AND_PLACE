#!/usr/bin/env python3
"""Splat-style 3D view from the arm camera's RGB-D: fuse the captures into coloured points, render them as round splats
from an orbiting virtual camera, save a GIF.

Not an optimised Gaussian splat (gsplat needs a CUDA compiler, which this machine does not have): the points come
straight from the depth image. One capture shows only the surfaces the camera saw; use several for more.

    python3 testing/splat_view.py --npz testing/_out/gn_cyl.npz --out assets/gifs/splat_view.gif
    python3 testing/splat_view.py --npz a.npz b.npz c.npz --center 0.35 0 0.1 --radius 0.5 --frames 60
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np

sys.path.append(str(Path.home() / ".local/lib/python3.10/site-packages"))
import cv2  # noqa: E402
from PIL import Image  # noqa: E402

OPT_FIX = np.array([[0, 0, 1, 0], [-1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 0, 1]], dtype=float)   # native -> optical frame


def points_from_capture(path, max_depth=1.6, stride=1):
    d = np.load(path)
    depth, rgb, K, T = d["depth"], d["rgb"], d["K"], d["T_base_cam"]
    if "optical" not in d.files:
        T = T @ OPT_FIX                      # older captures stored the native camera frame
    ok = np.isfinite(depth) & (depth > 0.1) & (depth < max_depth)
    v, u = np.nonzero(ok)
    v, u = v[::stride], u[::stride]
    z = depth[v, u].astype(float)
    cam = np.c_[(u - K[0, 2]) * z / K[0, 0], (v - K[1, 2]) * z / K[1, 1], z, np.ones_like(z)]
    return (T @ cam.T).T[:, :3], rgb[v, u].astype(np.uint8), z


def look_at(eye, target, up=(0, 0, 1)):
    f = np.asarray(target, float) - eye
    f /= np.linalg.norm(f)
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    R = np.stack([r, -u, f])                 # world -> camera (x right, y down, z forward)
    return R, -R @ eye


def render(pts, cols, R, t, f, W, H, point_px):
    cam = pts @ R.T + t
    z = cam[:, 2]
    keep = z > 0.05
    cam, z, c = cam[keep], z[keep], cols[keep]
    px = (f * cam[:, 0] / z + W / 2).astype(int)
    py = (f * cam[:, 1] / z + H / 2).astype(int)
    inb = (px >= 0) & (px < W) & (py >= 0) & (py < H)
    px, py, z, c = px[inb], py[inb], z[inb], c[inb]
    order = np.argsort(-z)                   # far to near: later (nearer) points overwrite
    px, py, z, c = px[order], py[order], z[order], c[order]
    img = np.full((H, W, 3), (235, 225, 215), np.uint8)
    rad = np.clip((point_px * f / z).astype(int), 0, 6)       # splat radius shrinks with distance
    for r in np.unique(rad):
        m = rad == r
        if r == 0:
            img[py[m], px[m]] = c[m]
        else:
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if dx * dx + dy * dy <= r * r:
                        yy, xx = np.clip(py[m] + dy, 0, H - 1), np.clip(px[m] + dx, 0, W - 1)
                        img[yy, xx] = c[m]
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--npz", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--center", nargs=3, type=float, help="orbit centre in base_link (default: the points' median)")
    ap.add_argument("--radius", type=float, default=0.55)
    ap.add_argument("--elevation", type=float, default=35.0, help="degrees above the horizon")
    ap.add_argument("--frames", type=int, default=48)
    ap.add_argument("--size", type=int, nargs=2, default=[560, 315])
    ap.add_argument("--span", type=float, default=140.0, help="degrees of orbit (centred on the camera's own side)")
    ap.add_argument("--crop", type=float, default=0.45, help="keep points within this distance (m) of the centre")
    args = ap.parse_args()

    P, C = [], []
    for p in args.npz:
        pts, cols, _ = points_from_capture(p)
        P.append(pts)
        C.append(cols)
    pts, cols = np.vstack(P), np.vstack(C)
    centre = np.array(args.center) if args.center else np.median(pts, 0)
    near = np.linalg.norm(pts - centre, axis=1) < args.crop
    pts, cols = pts[near], cols[near]
    print(f"{len(pts)} points within {args.crop} m of {np.round(centre, 3)}")

    W, H = args.size
    f = 0.9 * W
    el = math.radians(args.elevation)
    frames = []
    for i in range(args.frames):
        az = math.radians(-args.span / 2 + args.span * i / max(1, args.frames - 1))
        # start looking from the side the camera was on (base_link -x), sweep around the object
        eye = centre + args.radius * np.array([-math.cos(el) * math.cos(az), -math.cos(el) * math.sin(az), math.sin(el)])
        R, t = look_at(eye, centre)
        frames.append(Image.fromarray(render(pts, cols, R, t, f, W, H, point_px=0.0035)))
    frames[0].save(args.out, save_all=True, append_images=frames[1:], duration=80, loop=0, optimize=True)
    print("saved", args.out, f"({len(frames)} frames)")


if __name__ == "__main__":
    main()
