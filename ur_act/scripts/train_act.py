#!/usr/bin/env python3
"""
Train an ACT (Action Chunking Transformer) policy on UR3 demonstrations.

Reads the same HDF5 format produced by ur_data_collector (joint_positions,
gripper_positions, rgb_images, actions).

Usage:
    python3 train_act.py --data_dir ~/ur3_demos --output_dir ~/act_policy
    python3 train_act.py --data_dir ~/ur3_demos --chunk_size 15 --epochs 200
"""

import argparse
import os
import sys
import glob
from pathlib import Path

try:
    import numpy as np
except ImportError:
    print("ERROR: numpy not installed. Run: pip3 install numpy"); sys.exit(1)

try:
    import h5py
except ImportError:
    print("ERROR: h5py not installed. Run: pip3 install h5py"); sys.exit(1)

try:
    import torch
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader, random_split
except ImportError:
    print("ERROR: PyTorch not installed."); sys.exit(1)

try:
    import torchvision
except ImportError:
    print("ERROR: torchvision not installed. Run: pip3 install torchvision"); sys.exit(1)

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ur_act.model import ACT, act_loss

try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    PLOT = True
except ImportError:
    PLOT = False


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class ACTDemoDataset(Dataset):
    """
    Each sample: (rgb, joints, action_chunk) where
      rgb:          (3, H, W) float32 in [0, 1]
      joints:       (7,)      float32 — arm(6) + gripper(1) at step t
      action_chunk: (chunk_size, 7) float32 — actions[t : t+chunk_size], padded at end
    """

    def __init__(self, data_dir: str, chunk_size: int = 10,
                 img_h: int = 240, img_w: int = 424):
        self.chunk_size = chunk_size
        self.img_h = img_h
        self.img_w = img_w
        self.samples = []

        data_dir = os.path.expanduser(data_dir)
        h5_files = sorted(glob.glob(os.path.join(data_dir, "*.h5")))
        if not h5_files:
            raise FileNotFoundError(
                f"No HDF5 files found in {data_dir}. "
                "Record demonstrations first with the DataCollectorNode."
            )

        print(f"Loading {len(h5_files)} episode(s) from {data_dir}")
        for path in h5_files:
            try:
                with h5py.File(path, "r") as f:
                    rgb   = f["rgb_images"][:]       # (N, H, W, 3) uint8
                    jp    = f["joint_positions"][:]   # (N, 6)
                    gp    = f["gripper_positions"][:] # (N, 1)
                    acts  = f["actions"][:]           # (N, 7)
                N = len(acts)
                joints_full = np.concatenate([jp, gp], axis=1).astype(np.float32)
                for t in range(N):
                    end = min(t + chunk_size, N)
                    chunk = acts[t:end].astype(np.float32)
                    # Pad last action if episode is shorter than chunk_size
                    if len(chunk) < chunk_size:
                        pad = np.tile(chunk[-1:], (chunk_size - len(chunk), 1))
                        chunk = np.concatenate([chunk, pad], axis=0)
                    self.samples.append((rgb[t], joints_full[t], chunk))
                print(f"  {os.path.basename(path)}: {N} steps → {N} samples")
            except Exception as e:
                print(f"  WARNING: could not load {path}: {e}")

        print(f"Total samples: {len(self.samples)}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        rgb_hwc, joints, chunk = self.samples[idx]
        rgb = rgb_hwc.astype(np.float32) / 255.0
        rgb = np.transpose(rgb, (2, 0, 1))   # (3, H, W)
        return (
            torch.from_numpy(rgb),
            torch.from_numpy(joints),
            torch.from_numpy(chunk),
        )


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(args):
    out = os.path.expanduser(args.output_dir)
    os.makedirs(out, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    dataset = ACTDemoDataset(args.data_dir, chunk_size=args.chunk_size,
                              img_h=args.image_height, img_w=args.image_width)

    val_n = max(1, int(len(dataset) * 0.1))
    train_n = len(dataset) - val_n
    train_set, val_set = random_split(
        dataset, [train_n, val_n],
        generator=torch.Generator().manual_seed(42),
    )
    print(f"Train: {train_n}  Val: {val_n}")

    workers = min(4, os.cpu_count() or 1)
    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True,
                               num_workers=workers, pin_memory=(device.type == "cuda"))
    val_loader   = DataLoader(val_set,   batch_size=args.batch_size, shuffle=False,
                               num_workers=workers, pin_memory=(device.type == "cuda"))

    model = ACT(
        action_dim=7,
        chunk_size=args.chunk_size,
        d_model=args.d_model,
        nhead=args.nhead,
        num_encoder_layers=args.enc_layers,
        num_decoder_layers=args.dec_layers,
        latent_dim=args.latent_dim,
        freeze_backbone=args.freeze_backbone,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable parameters: {total_params:,}")

    optimizer = optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    train_losses, val_losses = [], []
    best_val = float("inf")

    print(f"\nTraining for {args.epochs} epochs  "
          f"chunk_size={args.chunk_size}  kl_weight={args.kl_weight}\n")

    for epoch in range(1, args.epochs + 1):
        # ── train ──
        model.train()
        ep_loss = ep_l1 = ep_kl = 0.0
        for rgb, joints, chunks in train_loader:
            rgb, joints, chunks = rgb.to(device), joints.to(device), chunks.to(device)
            optimizer.zero_grad()
            pred, mu, log_var = model(rgb, joints, actions=chunks)
            loss, l1, kl = act_loss(pred, chunks, mu, log_var, args.kl_weight)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            ep_loss += loss.item() * len(rgb)
            ep_l1   += l1 * len(rgb)
            ep_kl   += kl * len(rgb)
        ep_loss /= train_n;  ep_l1 /= train_n;  ep_kl /= train_n

        # ── val ──
        model.eval()
        v_loss = 0.0
        with torch.no_grad():
            for rgb, joints, chunks in val_loader:
                rgb, joints, chunks = rgb.to(device), joints.to(device), chunks.to(device)
                pred, mu, log_var = model(rgb, joints, actions=chunks)
                loss, _, _ = act_loss(pred, chunks, mu, log_var, args.kl_weight)
                v_loss += loss.item() * len(rgb)
        v_loss /= val_n
        scheduler.step()

        train_losses.append(ep_loss)
        val_losses.append(v_loss)

        print(f"Epoch {epoch:4d}/{args.epochs}  "
              f"loss={ep_loss:.5f}  l1={ep_l1:.5f}  kl={ep_kl:.5f}  "
              f"val={v_loss:.5f}  lr={scheduler.get_last_lr()[0]:.2e}")

        if v_loss < best_val:
            best_val = v_loss
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_loss": best_val,
                "args": vars(args),
            }, os.path.join(out, "best_act_policy.pt"))
            print(f"  -> saved best (val={best_val:.5f})")

        if epoch % 20 == 0:
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_loss": v_loss,
                "args": vars(args),
            }, os.path.join(out, f"act_epoch_{epoch:04d}.pt"))

    torch.save({
        "epoch": args.epochs,
        "model_state_dict": model.state_dict(),
        "val_loss": val_losses[-1],
        "args": vars(args),
    }, os.path.join(out, "final_act_policy.pt"))
    print(f"\nFinal model: {out}/final_act_policy.pt")
    print(f"Best val loss: {best_val:.5f}")

    if PLOT:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(train_losses, label="Train")
        ax.plot(val_losses,   label="Val")
        ax.set_xlabel("Epoch"); ax.set_ylabel("Loss"); ax.set_yscale("log")
        ax.set_title("ACT Training"); ax.legend(); ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(out, "act_training_curves.png"), dpi=150)
        plt.close()
        print(f"Curves: {out}/act_training_curves.png")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--data_dir",       default="~/ur3_demos")
    p.add_argument("--output_dir",     default="~/act_policy")
    p.add_argument("--epochs",   type=int,   default=100)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--lr",       type=float, default=1e-4)
    p.add_argument("--chunk_size", type=int, default=10,
                   help="Number of future actions to predict per step")
    p.add_argument("--kl_weight",  type=float, default=10.0)
    p.add_argument("--d_model",    type=int,   default=256)
    p.add_argument("--nhead",      type=int,   default=8)
    p.add_argument("--enc_layers", type=int,   default=4)
    p.add_argument("--dec_layers", type=int,   default=4)
    p.add_argument("--latent_dim", type=int,   default=32)
    p.add_argument("--image_height", type=int, default=240)
    p.add_argument("--image_width",  type=int, default=424)
    p.add_argument("--freeze_backbone", action="store_true",
                   help="Freeze ResNet18 weights during training")
    return p.parse_args()


if __name__ == "__main__":
    train(parse_args())
