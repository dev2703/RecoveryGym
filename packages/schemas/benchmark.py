from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from schemas.failure import FailureSpec
from schemas.task import TaskId


class BenchmarkProfile(str, Enum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    OOD = "ood"


PROFILE_EPISODES: dict[BenchmarkProfile, int] = {
    BenchmarkProfile.QUICK: 100,
    BenchmarkProfile.STANDARD: 1000,
    BenchmarkProfile.DEEP: 10000,
    BenchmarkProfile.OOD: 200,
}


class BenchmarkStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RunRequest(BaseModel):
    policy_id: str = "nominal"
    task_id: TaskId = TaskId.PICK_PLACE_V1
    failure: FailureSpec | None = None
    recovery: bool = True
    seed: int = 42


class BenchmarkRequest(BaseModel):
    policy_id: str = "nominal"
    task_id: TaskId = TaskId.PICK_PLACE_V1
    profile: BenchmarkProfile = BenchmarkProfile.QUICK
    episodes: int | None = None
    recovery: bool = True
    compare_baseline: bool = True


class BenchmarkResult(BaseModel):
    benchmark_id: str
    status: BenchmarkStatus
    profile: BenchmarkProfile
    progress: float = 0.0
    episodes_completed: int = 0
    episodes_total: int = 0
    metrics: dict[str, Any] = Field(default_factory=dict)
    baseline_metrics: dict[str, Any] = Field(default_factory=dict)
    recovery_metrics: dict[str, Any] = Field(default_factory=dict)
    ood_metrics: dict[str, Any] = Field(default_factory=dict)
    version_info: dict[str, str] = Field(default_factory=dict)
    error: str | None = None
