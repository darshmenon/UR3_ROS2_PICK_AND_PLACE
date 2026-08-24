#!/usr/bin/env python3
"""
Flow-matching training script for the DINOv2 action-chunk policy.

Trains FlowMatchingPolicy (ur_flow_policy.model) on HDF5 demonstration files
recorded by ur_data_collector's DataCollectorNode — same file schema as
ur_data_collector/scripts/train_bc.py (rgb_images, joint_positions,
gripper_positions, actions), windowed into overlapping action chunks.

Usage:
    python3 train_flow_policy.py --data_dir ~/ur3_demos --output_dir ~/flow_policy \
        --epochs 100 --chunk_size 16 --dinov2_backbone facebook/dinov2-base
"""

import argparse
import glob
import os
import sys

try:
    import numpy as np
except ImportError:
    print('ERROR: numpy not installed. Run: pip3 install numpy')
    sys.exit(1)

try:
    import h5py
except ImportError:
    print('ERROR: h5py not installed. Run: pip3 install h5py')
    sys.exit(1)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader, random_split
except ImportError:
    print('ERROR: PyTorch not installed.')
    sys.exit(1)

try:
    from transformers import AutoImageProcessor
except ImportError:
    print('ERROR: transformers not installed. Run: pip3 install transformers')
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ur_flow_policy.model import FlowMatchingPolicy


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class ActionChunkDataset(Dataset):
    """
    Loads HDF5 episodes and windows them into overlapping action chunks.

    Each sample is (rgb_uint8, proprio, action_chunk):
      - rgb_uint8:    (H, W, 3) uint8       — DINOv2 preprocessing happens in the training loop
      - proprio:      (7,)      float32     = [joint_positions(6), gripper_position(1)]
      - action_chunk: (chunk_size, 7) float32, padded by repeating the last
                       action when an episode ends before chunk_size steps remain
    """

    def __init__(self, data_dir: str, chunk_size: int):
        self.chunk_size = chunk_size
        self.data_dir = os.path.expanduser(data_dir)
        self.samples = []

        h5_files = sorted(glob.glob(os.path.join(self.data_dir, '*.h5')))
        if not h5_files:
            raise FileNotFoundError(
                f'No HDF5 files found in {self.data_dir}. '
                'Record demonstrations first with the DataCollectorNode.'
            )

        print(f'Loading {len(h5_files)} episode(s) from {self.data_dir}')
        total_steps = 0
        for filepath in h5_files:
            try:
                with h5py.File(filepath, 'r') as f:
                    rgb_images = f['rgb_images'][:]              # (N, H, W, 3) uint8
                    joint_positions = f['joint_positions'][:]    # (N, 6) float32
                    gripper_positions = f['gripper_positions'][:]  # (N, 1) float32
                    actions = f['actions'][:]                    # (N, 7) float32

                n_steps = len(actions)
                for i in range(n_steps):
                    proprio = np.concatenate(
                        [joint_positions[i], gripper_positions[i]]
                    ).astype(np.float32)  # (7,)

                    end = i + self.chunk_size
                    if end <= n_steps:
                        chunk = actions[i:end]
                    else:
                        pad = np.repeat(actions[n_steps - 1: n_steps], end - n_steps, axis=0)
                        chunk = np.concatenate([actions[i:n_steps], pad], axis=0)
                    chunk = chunk.astype(np.float32)  # (chunk_size, 7)

                    self.samples.append((rgb_images[i], proprio, chunk))

                total_steps += n_steps
                print(f'  {os.path.basename(filepath)}: {n_steps} steps')
            except Exception as e:
                print(f'  WARNING: Could not load {filepath}: {e}')

        print(f'Total windowed samples: {total_steps}')

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        rgb, proprio, chunk = self.samples[idx]
        return rgb, torch.from_numpy(proprio), torch.from_numpy(chunk)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(args):
    output_dir = os.path.expanduser(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'Using device: {device}')

    dataset = ActionChunkDataset(args.data_dir, chunk_size=args.chunk_size)
    val_size = max(1, int(len(dataset) * 0.1))
    train_size = len(dataset) - val_size
    train_set, val_set = random_split(
        dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42),
    )
    print(f'Train samples: {train_size}, Val samples: {val_size}')

    def collate(batch):
        rgbs = [b[0] for b in batch]
        proprio = torch.stack([b[1] for b in batch])
        chunks = torch.stack([b[2] for b in batch])
        return rgbs, proprio, chunks

    train_loader = DataLoader(
        train_set, batch_size=args.batch_size, shuffle=True,
        num_workers=min(4, os.cpu_count() or 1), collate_fn=collate,
    )
    val_loader = DataLoader(
        val_set, batch_size=args.batch_size, shuffle=False,
        num_workers=min(4, os.cpu_count() or 1), collate_fn=collate,
    )

    processor = AutoImageProcessor.from_pretrained(args.dinov2_backbone)

    model = FlowMatchingPolicy(
        chunk_size=args.chunk_size,
        action_dim=7,
        proprio_dim=7,
        hidden_dim=args.hidden_dim,
        depth=args.depth,
        dinov2_backbone=args.dinov2_backbone,
    ).to(device)

    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f'Trainable parameters: {trainable_params:,} / {total_params:,} total (DINOv2 backbone frozen)')

    optimizer = optim.Adam(
        (p for p in model.parameters() if p.requires_grad), lr=args.lr, weight_decay=1e-4,
    )
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    def flow_matching_loss(rgbs, proprio, action_chunk):
        pixel_values = processor(images=list(rgbs), return_tensors='pt')['pixel_values'].to(device)
        proprio = proprio.to(device)
        action_chunk = action_chunk.to(device)

        B = action_chunk.shape[0]
        t = torch.rand(B, device=device)
        noise = torch.randn_like(action_chunk)
        t_expand = t[:, None, None]
        x_t = (1 - t_expand) * noise + t_expand * action_chunk
        target_velocity = action_chunk - noise

        pred_velocity = model(pixel_values, proprio, x_t, t)
        return nn.functional.mse_loss(pred_velocity, target_velocity)

    train_losses, val_losses = [], []
    best_val_loss = float('inf')

    print(f'\nStarting training for {args.epochs} epoch(s)...\n')
    for epoch in range(1, args.epochs + 1):
        model.train()
        epoch_train_loss = 0.0
        for rgbs, proprio, chunks in train_loader:
            optimizer.zero_grad()
            loss = flow_matching_loss(rgbs, proprio, chunks)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_train_loss += loss.item() * len(rgbs)
        epoch_train_loss /= train_size

        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for rgbs, proprio, chunks in val_loader:
                loss = flow_matching_loss(rgbs, proprio, chunks)
                epoch_val_loss += loss.item() * len(rgbs)
        epoch_val_loss /= val_size

        scheduler.step()
        train_losses.append(epoch_train_loss)
        val_losses.append(epoch_val_loss)

        print(
            f'Epoch {epoch:4d}/{args.epochs} | '
            f'Train Loss: {epoch_train_loss:.6f} | '
            f'Val Loss: {epoch_val_loss:.6f} | '
            f'LR: {scheduler.get_last_lr()[0]:.2e}'
        )

        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            torch.save(
                {
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'val_loss': best_val_loss,
                    'args': vars(args),
                },
                os.path.join(output_dir, 'best_policy.pt'),
            )
            print(f'  -> Saved best checkpoint (val_loss={best_val_loss:.6f})')

    torch.save(
        {
            'epoch': args.epochs,
            'model_state_dict': model.state_dict(),
            'val_loss': val_losses[-1],
            'args': vars(args),
        },
        os.path.join(output_dir, 'final_policy.pt'),
    )
    print(f'\nFinal model saved to: {os.path.join(output_dir, "final_policy.pt")}')
    print(f'Best validation loss: {best_val_loss:.6f}')

    if MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(10, 5))
        epochs_range = range(1, args.epochs + 1)
        ax.plot(epochs_range, train_losses, label='Train Loss', linewidth=2)
        ax.plot(epochs_range, val_losses, label='Val Loss', linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('Flow-matching MSE Loss')
        ax.set_title('Flow-Matching Policy Training Curves')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')
        curves_path = os.path.join(output_dir, 'training_curves.png')
        plt.tight_layout()
        plt.savefig(curves_path, dpi=150)
        plt.close()
        print(f'Training curves saved to: {curves_path}')


def parse_args():
    parser = argparse.ArgumentParser(
        description='Train the DINOv2 flow-matching action-chunk policy on UR3 demonstrations.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--data_dir', type=str, default='~/ur3_demos')
    parser.add_argument('--output_dir', type=str, default='~/flow_policy')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch_size', type=int, default=16)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--chunk_size', type=int, default=16)
    parser.add_argument('--hidden_dim', type=int, default=256)
    parser.add_argument('--depth', type=int, default=6)
    parser.add_argument(
        '--dinov2_backbone', type=str, default='facebook/dinov2-base',
        choices=['facebook/dinov2-small', 'facebook/dinov2-base'],
    )
    return parser.parse_args()


if __name__ == '__main__':
    train(parse_args())
