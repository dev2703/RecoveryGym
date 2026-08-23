from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from schemas.failure import FailureEvent
from schemas.trajectory import EpisodeEvent, Trajectory


class EpisodeOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"


class EpisodeArtifact(BaseModel):
    episode_id: str
    task_id: str
    seed: int
    embodiment: str = "local_kinematic"
    initial_state: dict[str, Any]
    nominal_trajectory: Trajectory | None = None
    perturbed_trajectory: Trajectory | None = None
    failure_event: FailureEvent | None = None
    failure_observation: dict[str, Any] = Field(default_factory=dict)
    expert_recovery: dict[str, Any] = Field(default_factory=dict)
    events: list[EpisodeEvent] = Field(default_factory=list)
    outcome: EpisodeOutcome = EpisodeOutcome.FAILURE
    recovery_score: float = 0.0
    metrics: dict[str, float] = Field(default_factory=dict)
    is_ood: bool = False
    counterfactual_available: bool = False
