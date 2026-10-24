#!/usr/bin/env python3
"""Turn a folder of camera frames (from capture_frames.py) into a small looping GIF for the README.

    python3 testing/capture_frames.py --out frames --period 0.3 --seconds 40      # while a trial runs
    python3 testing/make_gif.py frames assets/pick_and_place.gif --width 400 --fps 6 --max-mb 2

Idle frames (nothing moves) are dropped, the rest are resized and quantised to a shared palette, and the frame count
is thinned until the file fits --max-mb.
"""
import argparse
import glob
from pathlib import Path

import numpy as np
from PIL import Image


def load(folder, width, crop=None):
    frames = []
    for f in sorted(glob.glob(str(Path(folder) / "*.png"))):
        im = Image.open(f).convert("RGB")
        if crop:
            im = im.crop(crop)
        h = int(im.height * width / im.width)
        frames.append(im.resize((width, h), Image.LANCZOS))
    return frames


def drop_idle(frames, threshold=1.5):
    """Keep a frame only if it differs from the last kept one (mean abs pixel difference above the threshold)."""
    kept = [frames[0]]
    for im in frames[1:]:
        if np.abs(np.asarray(im, dtype=np.int16) - np.asarray(kept[-1], dtype=np.int16)).mean() > threshold:
            kept.append(im)
    return kept


def save(frames, out, fps):
    pal = frames[len(frames) // 2].quantize(colors=128, method=Image.MEDIANCUT)
    q = [im.quantize(palette=pal, dither=Image.NONE) for im in frames]
    q[0].save(out, save_all=True, append_images=q[1:], duration=int(1000 / fps), loop=0, optimize=True, disposal=1)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("frames", help="folder with PNG frames")
    ap.add_argument("out")
    ap.add_argument("--width", type=int, default=400)
    ap.add_argument("--fps", type=float, default=6.0)
    ap.add_argument("--max-mb", type=float, default=2.0)
    ap.add_argument("--crop", default=None, help="x0,y0,x1,y1 in source pixels, applied before resizing")
    ap.add_argument("--keep-idle", action="store_true")
    ap.add_argument("--pause-end", type=float, default=1.5, help="seconds to hold the last frame")
    args = ap.parse_args()

    frames = load(args.frames, args.width, tuple(int(v) for v in args.crop.split(",")) if args.crop else None)
    if not frames:
        raise SystemExit("no frames found")
    if not args.keep_idle:
        frames = drop_idle(frames)
    step = 1
    while True:
        use = frames[::step]
        use = use + [use[-1]] * int(args.pause_end * args.fps)
        save(use, args.out, args.fps)
        mb = Path(args.out).stat().st_size / 1e6
        if mb <= args.max_mb or len(use) < 12:
            break
        step += 1
    print(f"{args.out}: {len(use)} frames, {mb:.2f} MB (kept every {step} frame(s), from {len(frames)} moving frames)")


if __name__ == "__main__":
    main()
