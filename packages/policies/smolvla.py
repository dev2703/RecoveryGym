"""SmolVLA adapters.

Both adapters are structural placeholders: they satisfy the RecoveryGym
interfaces and normalise actions, but the recovery behaviour still comes from
the rule primitives until a real checkpoint is wired in. Nothing here should be
reported as a learned result.
"""

from __future__ import annotations

from typing import Any

from core.recovery.rule_recovery import RuleRecoveryPolicy
from policies.nominal import NominalPolicy
from schemas.failure import FailureType
from schemas.task import TaskConfig

DEFAULT_MODEL_ID = "lerobot/smolvla_base"


class SmolVLAProvider:
    """Policy adapter. Zero-shot behaviour is the scripted nominal controller."""

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
    ):
        self.model_id = model_id
        self.checkpoint = checkpoint
        self.fine_tuned = fine_tuned
        self._controller = NominalPolicy()

    def reset(self, task: TaskConfig) -> dict[str, Any]:
        return self._controller.reset(task)

    def act(self, observation: dict[str, Any], instruction: str) -> dict[str, Any]:
        action = self._controller.act(observation, instruction)
        return {
            "dx": action["dx"],
            "dy": action["dy"],
            "toggle_gripper": action["toggle_gripper"],
            "source": "smolvla_finetuned" if self.fine_tuned else "smolvla_zeroshot",
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
    """Recovery adapter for a fine-tuned checkpoint.

    Second adapter at the recovery seam alongside RuleRecoveryPolicy. Action
    generation currently delegates to the rule primitives.
    """

    name = "SMOLVLA_RECOVERY"

    def __init__(self, checkpoint: str | None = "smolvla-recovery-v1"):
        self.checkpoint = checkpoint
        self._primitives = RuleRecoveryPolicy()

    def start(self, failure_type: FailureType) -> list[str]:
        return self._primitives.start(failure_type)

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        action = self._primitives.act(observation)
        action["source"] = "smolvla_recovery"
        return action

    def is_done(self) -> bool:
        return self._primitives.is_done()
