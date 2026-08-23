from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TrajectoryStep(BaseModel):
    t: int
    state: dict[str, Any]
    action: dict[str, Any]
    observation: dict[str, Any] = Field(default_factory=dict)


class Trajectory(BaseModel):
    steps: list[TrajectoryStep] = Field(default_factory=list)

    def append(self, step: TrajectoryStep) -> None:
        self.steps.append(step)


class EpisodeEvent(BaseModel):
    t: int
    event: str
    failure_type: str | None = None
    confidence: float | None = None
    policy: str | None = None
    success: bool | None = None
    details: dict[str, Any] = Field(default_factory=dict)
