"""Lazy SmolVLA inference engine with optional LeRobot backend."""

from __future__ import annotations

import logging
import os
from typing import Any

import numpy as np

from core.config import get_settings
from core.rendering.topdown import render_topdown

logger = logging.getLogger(__name__)

_ENGINE: "SmolVLAEngine | None" = None


class SmolVLAEngine:
    def __init__(
        self,
        model_id: str,
        checkpoint: str | None = None,
        device: str = "auto",
        allow_fallback: bool = False,
    ):
        self.model_id = checkpoint or model_id
        self.device = device
        self.allow_fallback = allow_fallback
        self._policy = None
        self._loaded = False
        self._load_error: str | None = None

    def _resolve_device(self) -> str:
        if self.device != "auto":
            return self.device
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        try:
            if get_settings().hf_token:
                os.environ.setdefault("HF_TOKEN", get_settings().hf_token or "")
                os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", get_settings().hf_token or "")

            from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy

            device = self._resolve_device()
            self._policy = SmolVLAPolicy.from_pretrained(self.model_id)
            self._policy.eval()
            self._policy.to(device)
            self._runtime_device = device
            logger.info("Loaded SmolVLA from %s on %s", self.model_id, device)
        except Exception as error:
            self._load_error = str(error)
            logger.warning("SmolVLA load failed: %s", error)
            if not self.allow_fallback:
                raise RuntimeError(f"SmolVLA load failed: {error}") from error

    def predict_action(self, observation: dict[str, Any], instruction: str) -> dict[str, float]:
        self._ensure_loaded()
        if self._policy is None:
            raise RuntimeError(self._load_error or "SmolVLA policy unavailable")

        import torch

        image = render_topdown(observation)
        image_t = torch.from_numpy(image).permute(2, 0, 1).float() / 255.0
        image_t = image_t.unsqueeze(0).to(self._runtime_device)

        state = torch.tensor(
            [
                [
                    observation["ee_x"],
                    observation["ee_y"],
                    observation["object_x"],
                    observation["object_y"],
                    observation["target_x"],
                    observation["target_y"],
                    float(observation.get("grasped", False)),
                    float(observation.get("gripper_open", True)),
                ]
            ],
            dtype=torch.float32,
            device=self._runtime_device,
        )

        batch = {
            "observation.images.top": image_t,
            "observation.state": state,
            "task": [instruction],
        }

        with torch.inference_mode():
            action = self._policy.select_action(batch)

        if isinstance(action, torch.Tensor):
            action = action.squeeze().detach().cpu().numpy()

        action = np.asarray(action).reshape(-1)
        dx = float(np.clip(action[0], -0.08, 0.08)) if action.size > 0 else 0.0
        dy = float(np.clip(action[1], -0.08, 0.08)) if action.size > 1 else 0.0
        grip = bool(action[2] > 0.5) if action.size > 2 else False
        return {"dx": dx, "dy": dy, "toggle_gripper": grip}


def get_engine(
    model_id: str | None = None,
    checkpoint: str | None = None,
    allow_fallback: bool | None = None,
) -> SmolVLAEngine:
    global _ENGINE
    cfg = get_settings()
    resolved_model = model_id or cfg.smolvla_model_id
    resolved_checkpoint = checkpoint or cfg.smolvla_checkpoint
    resolved_fallback = (
        cfg.smolvla_allow_fallback if allow_fallback is None else allow_fallback
    )
    key = (resolved_model, resolved_checkpoint, resolved_fallback)
    if _ENGINE is None or (
        _ENGINE.model_id,
        getattr(_ENGINE, "checkpoint", None),
        _ENGINE.allow_fallback,
    ) != key:
        _ENGINE = SmolVLAEngine(
            model_id=resolved_model,
            checkpoint=resolved_checkpoint,
            device=cfg.smolvla_device,
            allow_fallback=resolved_fallback,
        )
    return _ENGINE
