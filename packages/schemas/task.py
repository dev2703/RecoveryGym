from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskId(str, Enum):
    PICK_PLACE_V1 = "pick_place_v1"


class TaskConfig(BaseModel):
    task_id: TaskId = TaskId.PICK_PLACE_V1
    instruction: str = "Pick up the object and place it in the target."
    object_position: tuple[float, float] = (0.3, 0.2)
    target_position: tuple[float, float] = (0.7, 0.6)
    workspace_bounds: tuple[float, float, float, float] = (0.0, 1.0, 0.0, 1.0)
    max_steps: int = 200
    tolerance: dict[str, float] = Field(
        default_factory=lambda: {
            "position_noise": 0.02,
            "grasp_distance": 0.05,
            "target_radius": 0.08,
        }
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
