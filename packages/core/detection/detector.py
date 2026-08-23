from __future__ import annotations

import math
from typing import Any

from schemas.failure import FailureType
from schemas.task import TaskConfig

MAX_VELOCITY = 0.08
OCCLUDED_SENTINEL = -1.0


class FailureDetector:
    """Layered detector: task invariants, then residual against a predicted state,
    then temporal persistence. Carries its own forward model so callers only
    supply what they observe."""

    def __init__(self, task: TaskConfig, persistence_threshold: int = 3):
        self.task = task
        self.persistence_threshold = persistence_threshold
        self._predicted: dict[str, Any] = {}
        self._residuals: list[float] = []

    def reset(self) -> None:
        self._predicted = {}
        self._residuals = []

    def observe(self, observation: dict[str, Any], action: dict[str, Any]) -> None:
        """Advance the forward model by the action the policy just committed to."""
        if not self._predicted:
            self._predicted = {
                "object_x": observation["object_x"],
                "object_y": observation["object_y"],
                "grasped": bool(observation.get("grasped", False)),
            }

        if action.get("toggle_gripper"):
            if self._predicted["grasped"]:
                self._predicted["grasped"] = False
            elif self._within_grasp_range(observation):
                self._predicted["grasped"] = True

        if self._predicted["grasped"]:
            dx = _clip(action.get("dx", 0.0))
            dy = _clip(action.get("dy", 0.0))
            self._predicted["object_x"] = observation["ee_x"] + dx
            self._predicted["object_y"] = observation["ee_y"] + dy

    def detect(
        self, observation: dict[str, Any]
    ) -> tuple[FailureType | None, float, dict[str, Any]]:
        if observation.get("occlusion"):
            return FailureType.OCCLUSION, 0.82, {"layer": "invariant"}

        if observation.get("obstacle") is not None:
            return FailureType.OBSTACLE_APPEARS, 0.85, {"layer": "invariant"}

        if self._target_moved(observation):
            return FailureType.TARGET_SHIFT, 0.88, {"layer": "invariant"}

        grasp_lost = self._predicted.get("grasped") and not observation.get("grasped", False)
        if grasp_lost:
            failure = (
                FailureType.OBJECT_SLIP
                if self._object_diverged(observation)
                else FailureType.GRASP_MISS
            )
            return failure, 0.94, {"layer": "invariant"}

        residual = self._residual(observation)
        self._residuals.append(residual)
        if self._persistent():
            return FailureType.ACTUATOR_DEVIATION, 0.70, {"layer": "residual+persistence"}

        return None, 0.0, {}

    def _within_grasp_range(self, observation: dict[str, Any]) -> bool:
        gap = math.hypot(
            observation["ee_x"] - observation["object_x"],
            observation["ee_y"] - observation["object_y"],
        )
        return gap <= self.task.tolerance["grasp_distance"]

    def _target_moved(self, observation: dict[str, Any]) -> bool:
        expected_x, expected_y = self.task.target_position
        drift = math.hypot(
            observation.get("target_x", expected_x) - expected_x,
            observation.get("target_y", expected_y) - expected_y,
        )
        return drift > self.task.tolerance["target_radius"]

    def _object_diverged(self, observation: dict[str, Any]) -> bool:
        return self._residual(observation) > self.task.tolerance["position_noise"]

    def _residual(self, observation: dict[str, Any]) -> float:
        if not self._predicted:
            return 0.0
        observed_x = observation.get("object_x", 0.0)
        if observed_x == OCCLUDED_SENTINEL:
            return 0.0
        return math.hypot(
            observed_x - self._predicted["object_x"],
            observation.get("object_y", 0.0) - self._predicted["object_y"],
        )

    def _persistent(self) -> bool:
        if len(self._residuals) < self.persistence_threshold:
            return False
        limit = self.task.tolerance["position_noise"] * 2
        return all(r > limit for r in self._residuals[-self.persistence_threshold :])


def _clip(value: float) -> float:
    return max(-MAX_VELOCITY, min(MAX_VELOCITY, value))
