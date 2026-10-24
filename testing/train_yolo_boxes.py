#!/usr/bin/env python3
"""Fine-tune a small YOLOv8 on the conveyor camera frames, labelled automatically by colour.

    python3 testing/train_yolo_boxes.py --frames /tmp/convfr --out /tmp/yolo_boxes --epochs 40
    python3 testing/train_yolo_boxes.py --frames /tmp/convfr --out /tmp/yolo_boxes --predict-gif detections.gif

The frames come from the showcase_cam_conveyor camera (960x540). Boxes on the belt are saturated red / yellow / green /
blue on a grey belt, so an HSV threshold gives the boxes' bounding boxes; the bins (also coloured) sit above the belt and
are excluded by --belt-top. The pretrained weights come from the Hugging Face hub (Ultralytics/YOLOv8).
"""
import argparse
import random
import shutil
from pathlib import Path

import cv2
import numpy as np

CLASSES = ["red", "yellow", "green", "blue"]
# OpenCV hue is 0-179
HUE = {"red": [(0, 8), (172, 179)], "yellow": [(20, 34)], "green": [(40, 80)], "blue": [(100, 130)]}


def label_frame(img, belt_top, min_area=450, max_area=4000):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1] > 110
    val = hsv[:, :, 2] > 60
    out = []
    for ci, name in enumerate(CLASSES):
        m = np.zeros(sat.shape, bool)
        for lo, hi in HUE[name]:
            m |= (hsv[:, :, 0] >= lo) & (hsv[:, :, 0] <= hi)
        m = (m & sat & val).astype(np.uint8)
        m[:belt_top] = 0
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, _, stats, _ = cv2.connectedComponentsWithStats(m)
        for k in range(1, n):
            x, y, w, h, area = stats[k]
            if min_area <= area <= max_area and 0.5 <= w / h <= 2.0:     # box-shaped; drops the thin orange belt-end post
                out.append((ci, x, y, w, h))
    return out


def build_dataset(frames, out, belt_top, val_frac=0.2, seed=0):
    out = Path(out)
    for sub in ("train", "val"):
        (out / "images" / sub).mkdir(parents=True, exist_ok=True)
        (out / "labels" / sub).mkdir(parents=True, exist_ok=True)
    files = sorted(Path(frames).glob("*.png"))
    random.Random(seed).shuffle(files)
    n_val = max(1, int(len(files) * val_frac))
    counts = {c: 0 for c in CLASSES}
    kept = 0
    for i, f in enumerate(files):
        img = cv2.imread(str(f))
        labels = label_frame(img, belt_top)
        if not labels:
            continue
        sub = "val" if i < n_val else "train"
        h, w = img.shape[:2]
        shutil.copy(f, out / "images" / sub / f.name)
        with open(out / "labels" / sub / (f.stem + ".txt"), "w") as fh:
            for ci, x, y, bw, bh in labels:
                counts[CLASSES[ci]] += 1
                fh.write(f"{ci} {(x + bw / 2) / w:.6f} {(y + bh / 2) / h:.6f} {bw / w:.6f} {bh / h:.6f}\n")
        kept += 1
    (out / "data.yaml").write_text(f"path: {out.resolve()}\ntrain: images/train\nval: images/val\nnames:\n" +
                                   "".join(f"  {i}: {c}\n" for i, c in enumerate(CLASSES)))
    print(f"dataset: {kept} labelled frames, boxes per class {counts}")
    return out / "data.yaml"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--belt-top", type=int, default=290, help="pixel row above which labels are ignored (the bins)")
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--predict-gif", default=None, help="write a GIF of the trained model's detections on the frames")
    ap.add_argument("--crop", default="200,170,800,470", help="x0,y0,x1,y1 crop for the detections GIF")
    args = ap.parse_args()

    from huggingface_hub import hf_hub_download
    from ultralytics import YOLO
    data = build_dataset(args.frames, args.out, args.belt_top)
    weights = hf_hub_download("Ultralytics/YOLOv8", "yolov8n.pt")
    model = YOLO(weights)
    model.train(data=str(data), epochs=args.epochs, imgsz=args.imgsz, batch=16, project=str(Path(args.out) / "runs"),
                name="boxes", exist_ok=True, verbose=False, plots=False)
    best = Path(args.out) / "runs" / "boxes" / "weights" / "best.pt"
    print("best weights:", best)
    metrics = YOLO(str(best)).val(data=str(data), verbose=False)
    print(f"val mAP50 {metrics.box.map50:.3f}  mAP50-95 {metrics.box.map:.3f}")

    if args.predict_gif:
        from PIL import Image
        m = YOLO(str(best))
        x0, y0, x1, y1 = [int(v) for v in args.crop.split(",")]
        frames = []
        for f in sorted(Path(args.frames).glob("*.png"))[::2]:
            res = m.predict(str(f), imgsz=args.imgsz, conf=0.4, verbose=False)[0]
            im = cv2.cvtColor(res.plot(line_width=2, font_size=0.5), cv2.COLOR_BGR2RGB)[y0:y1, x0:x1]
            frames.append(Image.fromarray(im).resize((640, int(640 * (y1 - y0) / (x1 - x0)))))
        frames[0].save(args.predict_gif, save_all=True, append_images=frames[1:], duration=120, loop=0, optimize=True)
        print("wrote", args.predict_gif, len(frames), "frames")


if __name__ == "__main__":
    main()
