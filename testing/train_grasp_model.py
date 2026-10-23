#!/usr/bin/env python3
"""Train small grasp models on data from collect_grasp_data.py.

  held     close-up image right after the fingers closed -> is the object really held?
           (use at runtime: if not, open and retry before lifting)
  quality  scan-pose image + the grasp offset/yaw that was tried -> will this grasp lift the object?
           (use at runtime: score a few candidate grasps, take the best)

    python3 testing/train_grasp_model.py --task held --data ~/grasp_data/2f85_cube --out ~/grasp_data/held.pt
    python3 testing/train_grasp_model.py --task quality --data ~/grasp_data/* --out ~/grasp_data/quality.pt

Splits by trial (80/20, fixed), prints accuracy / AUC against the "always predict the majority" baseline.
"""
import argparse
import json
import math
import random
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn

IMG_W, IMG_H = 160, 90


def load_image(path):
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)
    img = cv2.resize(img, (IMG_W, IMG_H), interpolation=cv2.INTER_AREA)
    return torch.from_numpy(img[:, :, ::-1].copy()).permute(2, 0, 1).float() / 255.0


def grasp_features(row):
    """Offset/yaw of the tried grasp. Yaw as sin/cos of 4x the angle: a box repeats every 90 deg."""
    g = row["grasp_yaw"]
    return torch.tensor([row["offset_xy"][0] * 20, row["offset_xy"][1] * 20,
                         math.sin(4 * g), math.cos(4 * g), row["offset_yaw"] * 3], dtype=torch.float32)


def load_samples(dirs, task):
    samples = []
    suffix = "close" if task == "held" else "scan"
    for d in dirs:
        d = Path(d).expanduser()
        if not (d / "data.jsonl").exists():     # e.g. a collection run that never got going
            print(f"skipping {d}: no data.jsonl")
            continue
        rows = [json.loads(line) for line in open(d / "data.jsonl")]
        for r in rows:
            if r["skipped"]:
                continue
            p = d / "frames" / f"{r['trial']:05d}_{suffix}.jpg"
            if p.exists():
                samples.append((p, r))
    return samples


class GraspNet(nn.Module):
    def __init__(self, n_extra=0):
        super().__init__()

        def block(i, o):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(),
                                 nn.MaxPool2d(2))

        self.conv = nn.Sequential(block(3, 16), block(16, 32), block(32, 64), block(64, 96),
                                  nn.AdaptiveAvgPool2d(1), nn.Flatten())
        self.head = nn.Sequential(nn.Linear(96 + n_extra, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, 1))

    def forward(self, img, extra=None):
        z = self.conv(img)
        if extra is not None:
            z = torch.cat([z, extra], dim=1)
        return self.head(z).squeeze(1)


def auc(scores, labels):
    """Probability a random positive outscores a random negative (0.5 = chance)."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def make_batches(items, task, device, bs, shuffle, augment):
    idx = list(range(len(items)))
    if shuffle:
        random.shuffle(idx)
    for s in range(0, len(idx), bs):
        chunk = [items[i] for i in idx[s:s + bs]]
        imgs = torch.stack([x[0] for x in chunk])
        if augment:   # brightness/contrast only: geometry carries the label, so no flips or crops
            imgs = (imgs * (1 + 0.2 * (torch.rand(len(chunk), 1, 1, 1) - 0.5))
                    + 0.1 * (torch.rand(len(chunk), 1, 1, 1) - 0.5)).clamp(0, 1)
        extra = torch.stack([x[1] for x in chunk]) if task == "quality" else None
        y = torch.tensor([x[2] for x in chunk], dtype=torch.float32)
        yield imgs.to(device), (extra.to(device) if extra is not None else None), y.to(device)


def evaluate(model, items, task, device):
    model.eval()
    scores, labels = [], []
    with torch.no_grad():
        for imgs, extra, y in make_batches(items, task, device, 64, False, False):
            scores += torch.sigmoid(model(imgs, extra)).cpu().tolist()
            labels += y.cpu().int().tolist()
    acc = sum((s > 0.5) == bool(y) for s, y in zip(scores, labels)) / max(1, len(labels))
    return acc, auc(scores, labels)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", choices=["held", "quality"], required=True)
    ap.add_argument("--data", nargs="+", required=True, help="collect_grasp_data.py output dirs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    samples = load_samples(args.data, args.task)
    if len(samples) < 20:
        sys.exit(f"only {len(samples)} usable samples -- collect more data first")
    items = [(load_image(p), grasp_features(r) if args.task == "quality" else None, r["label"])
             for p, r in samples]
    order = sorted(range(len(items)), key=lambda i: samples[i][1]["trial"] * 7919 % 1000)
    cut = int(0.8 * len(order))
    train = [items[i] for i in order[:cut]]
    test = [items[i] for i in order[cut:]]
    pos = sum(x[2] for x in train) / len(train)
    base = max(sum(x[2] for x in test) / len(test), 1 - sum(x[2] for x in test) / len(test))
    print(f"{len(train)} train / {len(test)} test, {100 * pos:.0f}% positive; "
          f"majority-class baseline accuracy {100 * base:.0f}%")

    model = GraspNet(5 if args.task == "quality" else 0).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-3)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.epochs)
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor((1 - pos) / max(pos, 1e-3)).to(device))
    best = (-1, None)
    for epoch in range(args.epochs):
        model.train()
        for imgs, extra, y in make_batches(train, args.task, device, 32, True, True):
            opt.zero_grad()
            loss = loss_fn(model(imgs, extra), y)
            loss.backward()
            opt.step()
        sched.step()
        acc, a = evaluate(model, test, args.task, device)
        if (a if a == a else acc) > best[0]:
            best = (a if a == a else acc, {k: v.cpu().clone() for k, v in model.state_dict().items()})
        if epoch % 5 == 4 or epoch == args.epochs - 1:
            print(f"epoch {epoch + 1:3d}  test acc {100 * acc:.0f}%  auc {a:.3f}")
    model.load_state_dict(best[1])
    acc, a = evaluate(model, test, args.task, device)
    print(f"best: test acc {100 * acc:.0f}% (baseline {100 * base:.0f}%), auc {a:.3f}")
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"task": args.task, "state": best[1], "img": (IMG_W, IMG_H),
                "test_acc": acc, "test_auc": a}, out)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
