from __future__ import annotations

import random

from schemas.failure import FailureSpec, FailureType

TRAIN_SEVERITY = (0.10, 0.60)
OOD_SEVERITY = (0.65, 0.85)

KNOWN_TYPES = [
    FailureType.OBJECT_SLIP,
    FailureType.GRASP_MISS,
    FailureType.TARGET_SHIFT,
    FailureType.ACTUATOR_DEVIATION,
    FailureType.SENSOR_NOISE,
    FailureType.OCCLUSION,
    FailureType.OBSTACLE_APPEARS,
]

# Held out of training entirely: unseen combinations and the top severity band.
OOD_TYPES = [FailureType.COMPOSITE_FAILURE, FailureType.OBJECT_SLIP]

SPLITS = ("train", "val", "test", "ood")


def is_ood_scenario(failure_type: FailureType, severity: float, seed: int) -> bool:
    if failure_type == FailureType.COMPOSITE_FAILURE:
        return True
    if severity >= OOD_SEVERITY[0]:
        return True
    return random.Random(seed).random() < 0.15


def assign_scenario_split(
    episode_idx: int, failure_type: FailureType, severity: float, seed: int
) -> str:
    if is_ood_scenario(failure_type, severity, seed):
        return "ood"
    position = episode_idx % 10
    if position < 7:
        return "train"
    if position < 8:
        return "val"
    return "test"


def sample_severity_for_split(split: str, rng: random.Random) -> float:
    band = OOD_SEVERITY if split == "ood" else TRAIN_SEVERITY
    return rng.uniform(*band)


def sample_failure_spec(split: str, seed: int) -> FailureSpec:
    """Single source of truth for what a split's scenarios look like."""
    rng = random.Random(seed)
    ood = split == "ood"
    failure_type = rng.choice(OOD_TYPES if ood else KNOWN_TYPES)
    return FailureSpec(
        type=failure_type,
        seed=seed,
        severity=sample_severity_for_split(split, rng),
        time=35.0 if ood else 28.0,
        deterministic=True,
    )
