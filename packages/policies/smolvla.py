"""SmolVLA adapters backed by LeRobot when available."""

from __future__ import annotations

import logging
from typing import Any

from core.config import get_settings
from core.recovery.rule_recovery import RuleRecoveryPolicy
from policies.nominal import NominalPolicy
from policies.smolvla_inference import SmolVLAEngine, get_engine
from schemas.failure import FailureType
from schemas.task import TaskConfig

logger = logging.getLogger(__name__)

DEFAULT_MODEL_ID = "lerobot/smolvla_base"


class SmolVLAProvider:
    """Policy adapter using SmolVLA inference when the model is loadable."""

    observation_space = {
        "type": "multimodal",
        "state_keys": ["ee_x", "ee_y", "object_x", "object_y"],
    }
    action_space = {"type": "continuous", "dim": 3}

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        checkpoint: str | None = None,
        fine_tuned: bool = False,
        allow_fallback: bool | None = None,
    ):
        cfg = get_settings()
        self.model_id = model_id
        self.checkpoint = checkpoint or (cfg.smolvla_checkpoint if fine_tuned else None)
        self.fine_tuned = fine_tuned
        self.allow_fallback = (
            cfg.smolvla_allow_fallback if allow_fallback is None else allow_fallback
        )
        self._fallback = NominalPolicy()
        self._engine: SmolVLAEngine | None = None
        self._using_fallback = False

    def _engine_or_fallback(self) -> SmolVLAEngine | None:
        if self._using_fallback:
            return None
        try:
            if self._engine is None:
                self._engine = get_engine(
                    model_id=self.model_id,
                    checkpoint=self.checkpoint,
                    allow_fallback=self.allow_fallback,
                )
            return self._engine
        except Exception as error:
            if not self.allow_fallback:
                raise
            logger.warning("SmolVLA unavailable, using scripted fallback: %s", error)
            self._using_fallback = True
            return None

    def reset(self, task: TaskConfig) -> dict[str, Any]:
        self._fallback.reset(task)
        return {"model_id": self.model_id, "checkpoint": self.checkpoint}

    def act(self, observation: dict[str, Any], instruction: str) -> dict[str, Any]:
        engine = self._engine_or_fallback()
        if engine is None:
            action = self._fallback.act(observation, instruction)
            source = "smolvla_fallback"
        else:
            try:
                action = engine.predict_action(observation, instruction)
                source = "smolvla_finetuned" if self.fine_tuned else "smolvla_zeroshot"
            except Exception as error:
                if not self.allow_fallback:
                    raise
                logger.warning("SmolVLA inference failed: %s", error)
                action = self._fallback.act(observation, instruction)
                source = "smolvla_fallback"

        return {
            "dx": action["dx"],
            "dy": action["dy"],
            "toggle_gripper": action["toggle_gripper"],
            "source": source,
            "model_id": self.model_id,
            "checkpoint": self.checkpoint,
        }

    def metadata(self) -> dict[str, Any]:
        return {
            "id": "smolvla_ft" if self.fine_tuned else "smolvla",
            "type": "foundation_vla",
            "model_id": self.model_id,
            "checkpoint": self.checkpoint or "pretrained",
            "fine_tuned": self.fine_tuned,
            "version": "1.0.0",
        }


class SmolVLARecovery:
    """Recovery adapter; uses rule primitives until a recovery checkpoint exists."""

    name = "SMOLVLA_RECOVERY"

    def __init__(self, checkpoint: str | None = None):
        cfg = get_settings()
        self.checkpoint = checkpoint or cfg.smolvla_checkpoint or "smolvla-recovery-v1"
        self._primitives = RuleRecoveryPolicy()

    def start(self, failure_type: FailureType) -> list[str]:
        return self._primitives.start(failure_type)

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        action = self._primitives.act(observation)
        action["source"] = "smolvla_recovery"
        action["checkpoint"] = self.checkpoint
        return action

    def is_done(self) -> bool:
        return self._primitives.is_done()
