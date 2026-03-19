#!/usr/bin/env python3
"""
Behavior Cloning training script for UR3 pick-and-place demonstrations.

Trains a small CNN + MLP policy on HDF5 demonstration files recorded by
the DataCollectorNode.

Usage:
    python3 train_bc.py --data_dir ~/ur3_demos --output_dir ~/bc_policy --epochs 50
"""

import argparse
import os
import sys
import glob

# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------
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
    print('Install with: pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cpu')
    print('Or for CUDA: pip3 install torch torchvision')
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for headless environments
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print('WARNING: matplotlib not installed. Training curves will not be saved.')
    print('Install with: pip3 install matplotlib')
    MATPLOTLIB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class DemonstrationDataset(Dataset):
    """
    Loads all HDF5 demonstration files from a directory.

    Each sample is (rgb_image, joint_positions, action) where:
      - rgb_image:       (3, H, W) float32, normalized to [0, 1]
      - joint_positions: (6,)      float32
      - action:          (7,)      float32 = [arm_joints(6), gripper(1)]
    """

    def __init__(self, data_dir: str):
        self.data_dir = os.path.expanduser(data_dir)
        self.samples = []  # List of (rgb, joints, action) tuples

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
                    rgb_images = f['rgb_images'][:]        # (N, H, W, 3) uint8
                    joint_positions = f['joint_positions'][:]  # (N, 6) float32
                    actions = f['actions'][:]              # (N, 7) float32

                n_steps = len(actions)
                for i in range(n_steps):
                    # Convert HWC uint8 → CHW float32 [0,1]
                    rgb = rgb_images[i].astype(np.float32) / 255.0
                    rgb = np.transpose(rgb, (2, 0, 1))     # (3, H, W)

                    joints = joint_positions[i].astype(np.float32)  # (6,)
                    action = actions[i].astype(np.float32)           # (7,)

                    self.samples.append((rgb, joints, action))

                total_steps += n_steps
                print(f'  {os.path.basename(filepath)}: {n_steps} steps')

            except Exception as e:
                print(f'  WARNING: Could not load {filepath}: {e}')

        print(f'Total samples: {total_steps}')

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        rgb, joints, action = self.samples[idx]
        return (
            torch.from_numpy(rgb),
            torch.from_numpy(joints),
            torch.from_numpy(action),
        )


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------

class BCPolicy(nn.Module):
    """
    Behavior cloning policy: small CNN over RGB + MLP over joint states.

    Architecture:
      CNN branch:   3 conv layers → global average pool → 128-dim feature
      Joint branch: linear → 64-dim feature
      Combined:     concat → MLP(256, 256) → 7 outputs (6 arm + 1 gripper)
    """

    def __init__(self, image_height: int = 240, image_width: int = 424,
                 joint_dim: int = 6, action_dim: int = 7):
        super().__init__()

        # CNN branch
        self.cnn = nn.Sequential(
            # Conv block 1
            nn.Conv2d(3, 32, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1),

            # Conv block 2
            nn.Conv2d(32, 64, kernel_size=5, stride=2, padding=2, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),

            # Conv block 3
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),

            # Global average pooling → fixed 128-dim vector regardless of input size
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.cnn_fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 128),
            nn.ReLU(inplace=True),
        )

        # Joint state branch
        self.joint_fc = nn.Sequential(
            nn.Linear(joint_dim, 64),
            nn.ReLU(inplace=True),
        )

        # Combined MLP head
        combined_dim = 128 + 64  # 192
        self.mlp = nn.Sequential(
            nn.Linear(combined_dim, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.1),
            nn.Linear(256, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.1),
            nn.Linear(256, action_dim),
        )

    def forward(self, rgb: torch.Tensor, joints: torch.Tensor) -> torch.Tensor:
        """
        Args:
            rgb:    (B, 3, H, W) float32 in [0, 1]
            joints: (B, 6)       float32
        Returns:
            actions: (B, 7) float32
        """
        cnn_feat = self.cnn_fc(self.cnn(rgb))      # (B, 128)
        joint_feat = self.joint_fc(joints)          # (B, 64)
        combined = torch.cat([cnn_feat, joint_feat], dim=1)  # (B, 192)
        return self.mlp(combined)                   # (B, 7)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(args):
    output_dir = os.path.expanduser(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Device
    # ------------------------------------------------------------------
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print(f'Using GPU: {torch.cuda.get_device_name(0)}')
    else:
        device = torch.device('cpu')
        print('Using CPU (no CUDA device found)')

    # ------------------------------------------------------------------
    # Dataset & DataLoaders
    # ------------------------------------------------------------------
    dataset = DemonstrationDataset(args.data_dir)

    val_size = max(1, int(len(dataset) * 0.1))
    train_size = len(dataset) - val_size
    train_set, val_set = random_split(
        dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(42),
    )

    print(f'Train samples: {train_size}, Val samples: {val_size}')

    train_loader = DataLoader(
        train_set,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=min(4, os.cpu_count() or 1),
        pin_memory=(device.type == 'cuda'),
    )
    val_loader = DataLoader(
        val_set,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=min(4, os.cpu_count() or 1),
        pin_memory=(device.type == 'cuda'),
    )

    # ------------------------------------------------------------------
    # Model, optimizer, loss
    # ------------------------------------------------------------------
    model = BCPolicy(
        image_height=args.image_height,
        image_width=args.image_width,
        joint_dim=6,
        action_dim=7,
    ).to(device)

    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f'Model parameters: {total_params:,}')

    optimizer = optim.Adam(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    criterion = nn.MSELoss()

    # ------------------------------------------------------------------
    # Training loop
    # ------------------------------------------------------------------
    train_losses = []
    val_losses = []
    best_val_loss = float('inf')

    print(f'\nStarting training for {args.epochs} epoch(s)...\n')

    for epoch in range(1, args.epochs + 1):
        # --- Train ---
        model.train()
        epoch_train_loss = 0.0
        for rgb, joints, actions in train_loader:
            rgb = rgb.to(device)
            joints = joints.to(device)
            actions = actions.to(device)

            optimizer.zero_grad()
            predictions = model(rgb, joints)
            loss = criterion(predictions, actions)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()

            epoch_train_loss += loss.item() * len(rgb)

        epoch_train_loss /= train_size

        # --- Validate ---
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for rgb, joints, actions in val_loader:
                rgb = rgb.to(device)
                joints = joints.to(device)
                actions = actions.to(device)
                predictions = model(rgb, joints)
                loss = criterion(predictions, actions)
                epoch_val_loss += loss.item() * len(rgb)

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

        # --- Save checkpoint if improved ---
        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            checkpoint_path = os.path.join(output_dir, 'best_policy.pt')
            torch.save(
                {
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_loss': best_val_loss,
                    'train_loss': epoch_train_loss,
                    'args': vars(args),
                },
                checkpoint_path,
            )
            print(f'  -> Saved best checkpoint (val_loss={best_val_loss:.6f})')

        # --- Periodic checkpoint every 10 epochs ---
        if epoch % 10 == 0:
            periodic_path = os.path.join(output_dir, f'checkpoint_epoch_{epoch:04d}.pt')
            torch.save(
                {
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'val_loss': epoch_val_loss,
                    'train_loss': epoch_train_loss,
                },
                periodic_path,
            )

    # ------------------------------------------------------------------
    # Save final model
    # ------------------------------------------------------------------
    final_path = os.path.join(output_dir, 'final_policy.pt')
    torch.save(
        {
            'epoch': args.epochs,
            'model_state_dict': model.state_dict(),
            'val_loss': val_losses[-1],
            'train_loss': train_losses[-1],
            'args': vars(args),
        },
        final_path,
    )
    print(f'\nFinal model saved to: {final_path}')
    print(f'Best validation loss:  {best_val_loss:.6f}')

    # ------------------------------------------------------------------
    # Plot training curves
    # ------------------------------------------------------------------
    if MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(10, 5))
        epochs_range = range(1, args.epochs + 1)
        ax.plot(epochs_range, train_losses, label='Train Loss', linewidth=2)
        ax.plot(epochs_range, val_losses, label='Val Loss', linewidth=2)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('MSE Loss')
        ax.set_title('Behavior Cloning Training Curves')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_yscale('log')

        curves_path = os.path.join(output_dir, 'training_curves.png')
        plt.tight_layout()
        plt.savefig(curves_path, dpi=150)
        plt.close()
        print(f'Training curves saved to: {curves_path}')
    else:
        print('Install matplotlib to save training curves: pip3 install matplotlib')


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description='Train a behavior cloning policy on UR3 demonstrations.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--data_dir',
        type=str,
        default='~/ur3_demos',
        help='Directory containing HDF5 demonstration files.',
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='~/bc_policy',
        help='Directory to save model checkpoints and plots.',
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=50,
        help='Number of training epochs.',
    )
    parser.add_argument(
        '--batch_size',
        type=int,
        default=32,
        help='Training batch size.',
    )
    parser.add_argument(
        '--lr',
        type=float,
        default=1e-3,
        help='Initial learning rate for Adam optimizer.',
    )
    parser.add_argument(
        '--image_height',
        type=int,
        default=240,
        help='Expected image height (must match recorded data).',
    )
    parser.add_argument(
        '--image_width',
        type=int,
        default=424,
        help='Expected image width (must match recorded data).',
    )
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    train(args)
