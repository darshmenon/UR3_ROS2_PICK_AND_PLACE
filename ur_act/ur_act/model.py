"""
ACT model: Action Chunking with Transformers.

Architecture (Zhao et al. 2023):
  Training:  CVAE encoder(joints, action_chunk) → z
             Transformer decoder(image_tokens, joint_token, z) → predicted_chunk
  Inference: z = 0
             Transformer decoder(image_tokens, joint_token, 0) → predicted_chunk

Loss = L1(predicted, target) + kl_weight * KL(q(z|obs,actions) || N(0,1))
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as tvm


# ---------------------------------------------------------------------------
# Visual backbone
# ---------------------------------------------------------------------------

class VisualBackbone(nn.Module):
    """ResNet18 → spatial tokens of shape (B, num_tokens, d_model)."""

    def __init__(self, d_model: int = 256, pool_hw: tuple = (6, 6), freeze: bool = False):
        super().__init__()
        resnet = tvm.resnet18(weights=tvm.ResNet18_Weights.DEFAULT)
        # Drop avgpool and fc; keep up to layer4 → (B, 512, H/32, W/32)
        self.backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.pool = nn.AdaptiveAvgPool2d(pool_hw)           # (B, 512, h, w)
        num_tokens = pool_hw[0] * pool_hw[1]
        self.proj = nn.Linear(512, d_model)
        self.pos_embed = nn.Parameter(torch.zeros(1, num_tokens, d_model))
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

        if freeze:
            for p in self.backbone.parameters():
                p.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, 3, H, W) → (B, num_tokens, d_model)"""
        feat = self.backbone(x)          # (B, 512, h', w')
        feat = self.pool(feat)           # (B, 512, pool_h, pool_w)
        B, C, h, w = feat.shape
        feat = feat.flatten(2).transpose(1, 2)   # (B, h*w, 512)
        feat = self.proj(feat) + self.pos_embed   # (B, num_tokens, d_model)
        return feat


# ---------------------------------------------------------------------------
# CVAE encoder (training only)
# ---------------------------------------------------------------------------

class CVAEEncoder(nn.Module):
    """
    Encodes (current_joints, action_sequence) → (mu, log_var).

    Uses a small transformer encoder with a learned CLS token.
    """

    def __init__(self, action_dim: int = 7, chunk_size: int = 10,
                 d_model: int = 256, nhead: int = 8, num_layers: int = 4,
                 latent_dim: int = 32):
        super().__init__()
        self.chunk_size = chunk_size
        self.d_model = d_model

        self.input_proj = nn.Linear(action_dim, d_model)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, d_model))
        # +1 for current joints token, +1 for CLS
        seq_len = chunk_size + 2
        self.pos_embed = nn.Parameter(torch.zeros(1, seq_len, d_model))
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        nn.init.trunc_normal_(self.pos_embed, std=0.02)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=d_model * 4,
            dropout=0.1, batch_first=True, norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.mu_head = nn.Linear(d_model, latent_dim)
        self.logvar_head = nn.Linear(d_model, latent_dim)

    def forward(self, joints: torch.Tensor, actions: torch.Tensor):
        """
        joints:  (B, action_dim) current joint state
        actions: (B, chunk_size, action_dim) target action chunk
        Returns: mu, log_var each (B, latent_dim)
        """
        B = joints.size(0)
        joint_tok = self.input_proj(joints).unsqueeze(1)          # (B, 1, d)
        action_tok = self.input_proj(actions)                       # (B, chunk_size, d)
        cls = self.cls_token.expand(B, -1, -1)                     # (B, 1, d)
        seq = torch.cat([cls, joint_tok, action_tok], dim=1)        # (B, chunk_size+2, d)
        seq = seq + self.pos_embed
        out = self.encoder(seq)                                     # (B, chunk_size+2, d)
        cls_out = out[:, 0]                                         # (B, d)
        return self.mu_head(cls_out), self.logvar_head(cls_out)


# ---------------------------------------------------------------------------
# ACT (full model)
# ---------------------------------------------------------------------------

class ACT(nn.Module):
    """
    Action Chunking Transformer.

    chunk_size: number of future actions to predict per forward pass
    kl_weight:  weight on the KL term (default 10.0 from the paper)
    """

    def __init__(
        self,
        action_dim: int = 7,
        chunk_size: int = 10,
        d_model: int = 256,
        nhead: int = 8,
        num_encoder_layers: int = 4,
        num_decoder_layers: int = 4,
        latent_dim: int = 32,
        pool_hw: tuple = (6, 6),
        freeze_backbone: bool = False,
    ):
        super().__init__()
        self.action_dim = action_dim
        self.chunk_size = chunk_size
        self.latent_dim = latent_dim
        self.d_model = d_model

        self.backbone = VisualBackbone(d_model, pool_hw, freeze=freeze_backbone)
        self.cvae_encoder = CVAEEncoder(action_dim, chunk_size, d_model, nhead,
                                        num_encoder_layers, latent_dim)

        # Project joint state → d_model
        self.joint_proj = nn.Linear(action_dim, d_model)
        # Project latent z → d_model
        self.z_proj = nn.Linear(latent_dim, d_model)

        # Learned query embeddings for decoder (one per chunk position)
        self.query_embed = nn.Parameter(torch.zeros(chunk_size, d_model))
        nn.init.trunc_normal_(self.query_embed, std=0.02)

        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=d_model * 4,
            dropout=0.1, batch_first=True, norm_first=True,
        )
        self.decoder = nn.TransformerDecoder(decoder_layer, num_layers=num_decoder_layers)
        self.action_head = nn.Linear(d_model, action_dim)

    def encode(self, joints: torch.Tensor, actions: torch.Tensor):
        """CVAE encode → reparameterize → z, mu, log_var"""
        mu, log_var = self.cvae_encoder(joints, actions)
        if self.training:
            std = (0.5 * log_var).exp()
            z = mu + std * torch.randn_like(std)
        else:
            z = torch.zeros_like(mu)
        return z, mu, log_var

    def decode(self, image: torch.Tensor, joints: torch.Tensor, z: torch.Tensor):
        """
        image:  (B, 3, H, W)
        joints: (B, action_dim)
        z:      (B, latent_dim)
        Returns: (B, chunk_size, action_dim)
        """
        B = image.size(0)
        img_tok = self.backbone(image)                             # (B, num_img_tokens, d)
        joint_tok = self.joint_proj(joints).unsqueeze(1)           # (B, 1, d)
        z_tok = self.z_proj(z).unsqueeze(1)                        # (B, 1, d)
        memory = torch.cat([img_tok, joint_tok, z_tok], dim=1)     # (B, M, d)

        queries = self.query_embed.unsqueeze(0).expand(B, -1, -1)  # (B, chunk_size, d)
        out = self.decoder(queries, memory)                         # (B, chunk_size, d)
        return self.action_head(out)                               # (B, chunk_size, action_dim)

    def forward(self, image: torch.Tensor, joints: torch.Tensor,
                actions: torch.Tensor | None = None):
        """
        Training: pass actions to get CVAE loss terms.
        Inference: actions=None, z=0.

        Returns:
          pred_actions: (B, chunk_size, action_dim)
          mu, log_var:  (B, latent_dim) — None during inference
        """
        if actions is not None:
            z, mu, log_var = self.encode(joints, actions)
        else:
            B = image.size(0)
            z = torch.zeros(B, self.latent_dim, device=image.device)
            mu, log_var = None, None

        pred = self.decode(image, joints, z)
        return pred, mu, log_var


# ---------------------------------------------------------------------------
# Loss
# ---------------------------------------------------------------------------

def act_loss(pred: torch.Tensor, target: torch.Tensor,
             mu: torch.Tensor, log_var: torch.Tensor,
             kl_weight: float = 10.0):
    """
    pred, target: (B, chunk_size, action_dim)
    mu, log_var:  (B, latent_dim)
    """
    l1 = F.l1_loss(pred, target)
    kl = -0.5 * (1 + log_var - mu.pow(2) - log_var.exp()).mean()
    return l1 + kl_weight * kl, l1.item(), kl.item()


# ---------------------------------------------------------------------------
# Temporal ensemble helper
# ---------------------------------------------------------------------------

class TemporalEnsemble:
    """
    Maintains overlapping ACT predictions and blends them with exponential weights.

    At each step:
      1. call push(new_chunk) — add the latest (chunk_size, action_dim) prediction
      2. call get()          — returns the blended action for the current step
    """

    def __init__(self, chunk_size: int, action_dim: int, gamma: float = 0.01):
        self.chunk_size = chunk_size
        self.action_dim = action_dim
        self.gamma = gamma
        self._queue: list[tuple[int, torch.Tensor]] = []  # (age_offset, chunk)
        self._step = 0

    def push(self, chunk: torch.Tensor):
        """chunk: (chunk_size, action_dim)"""
        self._queue.append((self._step, chunk.clone()))
        # Drop predictions that no longer cover the current step
        self._queue = [(t, c) for t, c in self._queue
                       if t + self.chunk_size > self._step]

    def get(self) -> torch.Tensor:
        """Returns blended action for current step, then advances the internal clock."""
        if not self._queue:
            raise RuntimeError("No predictions in queue — call push() first.")

        weights, actions = [], []
        for start_t, chunk in self._queue:
            idx = self._step - start_t
            if 0 <= idx < self.chunk_size:
                age = len(self._queue) - 1 - self._queue.index((start_t, chunk))
                w = math.exp(-self.gamma * age)
                weights.append(w)
                actions.append(chunk[idx])

        w_sum = sum(weights)
        blended = sum(w * a for w, a in zip(weights, actions)) / w_sum
        self._step += 1
        return blended
