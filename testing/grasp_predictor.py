"""Use models trained by train_grasp_model.py at run time.

    from grasp_predictor import GraspPredictor
    held = GraspPredictor("~/grasp_data/held.pt")          # task "held"
    p = held.held_probability(close_up_bgr_image)          # > 0.5: the object is really held, lift it
    quality = GraspPredictor("~/grasp_data/quality.pt")    # task "quality"
    best = quality.best_grasp(scan_bgr_image, candidates)  # candidates: [(offset_x, offset_y, grasp_yaw), ...]

Offsets are in metres, relative to the detected object centre; yaw in radians, relative to the object.
"""
import math
from pathlib import Path

import cv2
import numpy as np
import torch

from train_grasp_model import GraspNet, IMG_H, IMG_W


class GraspPredictor:
    def __init__(self, path, device=None):
        ckpt = torch.load(Path(path).expanduser(), map_location="cpu")
        self.task = ckpt["task"]
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = GraspNet(5 if self.task == "quality" else 0).to(self.device)
        self.model.load_state_dict(ckpt["state"])
        self.model.eval()
        self.test_auc = ckpt.get("test_auc")

    @staticmethod
    def _image(bgr):
        img = cv2.resize(bgr, (IMG_W, IMG_H), interpolation=cv2.INTER_AREA)
        return torch.from_numpy(img[:, :, ::-1].copy()).permute(2, 0, 1).float().div(255.0)

    def held_probability(self, close_bgr):
        """Probability the object is held, from a close-up taken right after the fingers closed."""
        assert self.task == "held", "this is a quality model"
        with torch.no_grad():
            x = self._image(close_bgr).unsqueeze(0).to(self.device)
            return float(torch.sigmoid(self.model(x))[0])

    def quality(self, scan_bgr, candidates):
        """Probability each candidate grasp (offset_x, offset_y, grasp_yaw) lifts the object."""
        assert self.task == "quality", "this is a held model"
        img = self._image(scan_bgr).unsqueeze(0).to(self.device)
        feats = torch.tensor([[ox * 20, oy * 20, math.sin(4 * g), math.cos(4 * g), g * 3]
                              for ox, oy, g in candidates], dtype=torch.float32, device=self.device)
        with torch.no_grad():
            return torch.sigmoid(self.model(img.expand(len(candidates), -1, -1, -1), feats)).cpu().tolist()

    def best_grasp(self, scan_bgr, candidates):
        scores = self.quality(scan_bgr, candidates)
        i = int(np.argmax(scores))
        return candidates[i], scores[i]
