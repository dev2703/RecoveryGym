from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FailureType(str, Enum):
    GRASP_MISS = "GRASP_MISS"
    OBJECT_SLIP = "OBJECT_SLIP"
    TARGET_SHIFT = "TARGET_SHIFT"
    ACTUATOR_DEVIATION = "ACTUATOR_DEVIATION"
    SENSOR_NOISE = "SENSOR_NOISE"
    OCCLUSION = "OCCLUSION"
    OBSTACLE_APPEARS = "OBSTACLE_APPEARS"
    COMPOSITE_FAILURE = "COMPOSITE_FAILURE"
    DISTRIBUTION_SHIFT = "DISTRIBUTION_SHIFT"


class FailureSpec(BaseModel):
    type: FailureType | None = None
    seed: int | None = None
    deterministic: bool = True
    severity: float | None = None
    time: float | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class FailureEvent(BaseModel):
    type: FailureType
    seed: int
    time: float
    severity: float
    step: int = 0
    direction: str | None = None
    sampled_params: dict[str, Any] = Field(default_factory=dict)
    components: list[FailureEvent] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
