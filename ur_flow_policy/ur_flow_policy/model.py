#!/usr/bin/env python3
"""
DINOv2 + flow-matching action-chunk policy.

Architecture:
  - DINOv2 ViT backbone (frozen) -> CLS token -> learned projection
  - Small MLP proprioception encoder (joint positions + gripper)
  - Sinusoidal embedding of the flow-matching ODE time t in [0, 1]
  - Transformer trunk fusing [image, proprio, time, noisy-action-chunk] tokens
  - MLP head predicting the flow-matching velocity for each action in the chunk

Inputs to the transformer are already-preprocessed pixel_values (ImageNet
normalized, as produced by transformers.AutoImageProcessor) — this module
does not do image I/O or normalization itself.
"""

import math

import torch
import torch.nn as nn

try:
    from transformers import AutoModel
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


DINOV2_HIDDEN_DIM = {
    "facebook/dinov2-small": 384,   # ViT-S/14
    "facebook/dinov2-base":  768,   # ViT-B/14
}


class SinusoidalTimeEmbedding(nn.Module):
    """Standard transformer sinusoidal embedding, applied to a scalar t in [0, 1]."""

    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        half = self.dim // 2
        freqs = torch.exp(
            -math.log(10000.0) * torch.arange(half, device=t.device, dtype=torch.float32) / half
        )
        args = t.float()[:, None] * freqs[None, :]
        emb = torch.cat([torch.sin(args), torch.cos(args)], dim=-1)
        if self.dim % 2:
            emb = torch.nn.functional.pad(emb, (0, 1))
        return emb


class DINOv2VisionEncoder(nn.Module):
    """Frozen DINOv2 backbone -> CLS token -> trainable projection to hidden_dim."""

    def __init__(self, hidden_dim: int, backbone: str = "facebook/dinov2-base"):
        super().__init__()
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError("transformers is required for DINOv2VisionEncoder")
        if backbone not in DINOV2_HIDDEN_DIM:
            raise ValueError(f"Unsupported DINOv2 backbone '{backbone}', expected one of {list(DINOV2_HIDDEN_DIM)}")

        self.backbone_name = backbone
        self.backbone = AutoModel.from_pretrained(backbone)
        for p in self.backbone.parameters():
            p.requires_grad = False
        self.backbone.eval()

        self.project = nn.Linear(DINOV2_HIDDEN_DIM[backbone], hidden_dim)

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            out = self.backbone(pixel_values=pixel_values)
        cls_token = out.last_hidden_state[:, 0]  # (B, backbone_hidden)
        return self.project(cls_token)            # (B, hidden_dim)


class FlowMatchingPolicy(nn.Module):
    """
    Predicts the flow-matching velocity field for an action chunk, conditioned
    on the current image and proprioceptive state.

    forward(pixel_values, proprio, noisy_actions, t) -> predicted_velocity
      pixel_values:  (B, 3, H, W)              DINOv2-preprocessed RGB image
      proprio:       (B, proprio_dim)          joint positions + gripper
      noisy_actions: (B, chunk_size, action_dim)  x_t along the flow path
      t:             (B,)                      ODE time in [0, 1]
      returns:       (B, chunk_size, action_dim)
    """

    def __init__(
        self,
        chunk_size: int = 16,
        action_dim: int = 7,
        proprio_dim: int = 7,
        hidden_dim: int = 256,
        depth: int = 6,
        n_heads: int = 8,
        dinov2_backbone: str = "facebook/dinov2-base",
    ):
        super().__init__()
        self.chunk_size = chunk_size
        self.action_dim = action_dim
        self.hidden_dim = hidden_dim

        self.vision = DINOv2VisionEncoder(hidden_dim, backbone=dinov2_backbone)
        self.proprio_encoder = nn.Sequential(
            nn.Linear(proprio_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, hidden_dim),
        )
        self.time_embed = SinusoidalTimeEmbedding(hidden_dim)
        self.action_in = nn.Linear(action_dim, hidden_dim)
        self.action_pos = nn.Parameter(torch.randn(1, chunk_size, hidden_dim) * 0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=n_heads,
            dim_feedforward=hidden_dim * 4,
            dropout=0.1,
            batch_first=True,
            activation="gelu",
        )
        self.trunk = nn.TransformerEncoder(encoder_layer, num_layers=depth)

        self.head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, action_dim),
        )

    def encode_image(self, pixel_values: torch.Tensor) -> torch.Tensor:
        """Runs the (frozen) DINOv2 backbone. Cache this once per control tick at
        inference time and reuse across ODE integration steps via image_features="""
        return self.vision(pixel_values)

    def forward(
        self,
        pixel_values: "torch.Tensor | None" = None,
        proprio: torch.Tensor = None,
        noisy_actions: torch.Tensor = None,
        t: torch.Tensor = None,
        image_features: "torch.Tensor | None" = None,
    ) -> torch.Tensor:
        if image_features is None:
            image_features = self.encode_image(pixel_values)
        image_tok = image_features[:, None, :]                      # (B, 1, H)
        proprio_tok = self.proprio_encoder(proprio)[:, None, :]     # (B, 1, H)
        time_tok = self.time_embed(t)[:, None, :]                   # (B, 1, H)
        action_tok = self.action_in(noisy_actions) + self.action_pos  # (B, chunk, H)

        tokens = torch.cat([image_tok, proprio_tok, time_tok, action_tok], dim=1)
        trunk_out = self.trunk(tokens)

        action_out = trunk_out[:, -self.chunk_size:, :]  # (B, chunk, H)
        return self.head(action_out)                      # (B, chunk, action_dim)
