from __future__ import annotations

import math
from typing import Any, Protocol

from core.recovery.primitives import RecoveryPrimitive as P
from schemas.failure import FailureType

FALLBACK_OBJECT = (0.3, 0.2)

RULE_MAP: dict[FailureType, list[P]] = {
    FailureType.OBJECT_SLIP: [P.STOP, P.MOVE_TO_OBJECT, P.REGRASP, P.VERIFY_GRASP, P.RESUME],
    FailureType.GRASP_MISS: [P.STOP, P.MOVE_TO_OBJECT, P.REGRASP, P.VERIFY_GRASP, P.RESUME],
    FailureType.TARGET_SHIFT: [P.STOP, P.REALIGN, P.VERIFY_TARGET, P.RESUME],
    FailureType.OCCLUSION: [P.STOP, P.MOVE_TO_OBJECT, P.RESUME],
    FailureType.OBSTACLE_APPEARS: [P.SAFE_STOP, P.REALIGN, P.RESUME],
    FailureType.SENSOR_NOISE: [P.STOP, P.MOVE_TO_OBJECT, P.VERIFY_GRASP, P.RESUME],
    FailureType.ACTUATOR_DEVIATION: [P.STOP, P.REALIGN, P.RESUME],
    FailureType.COMPOSITE_FAILURE: [
        P.SAFE_STOP,
        P.MOVE_TO_OBJECT,
        P.REGRASP,
        P.VERIFY_GRASP,
        P.RESUME,
    ],
}


def get_recovery_plan(failure_type: FailureType) -> list[str]:
    return [p.value for p in RULE_MAP.get(failure_type, [P.SAFE_STOP])]


class RecoveryPolicy(Protocol):
    """Seam for recovery behaviour: rules today, learned or foundation adapters later."""

    name: str

    def start(self, failure_type: FailureType) -> list[str]: ...

    def act(self, observation: dict[str, Any]) -> dict[str, Any]: ...

    def is_done(self) -> bool: ...


class RuleRecoveryPolicy:
    """Deterministic primitive sequence executed as low-level actions."""

    name = "RULE_RECOVERY"

    def __init__(self) -> None:
        self.plan: list[str] = []
        self.step_idx = 0

    def start(self, failure_type: FailureType) -> list[str]:
        self.plan = get_recovery_plan(failure_type)
        self.step_idx = 0
        return self.plan

    def is_done(self) -> bool:
        return self.step_idx >= len(self.plan)

    def act(self, observation: dict[str, Any]) -> dict[str, Any]:
        if self.is_done():
            return _hold()

        primitive = self.plan[self.step_idx]
        ee = (observation["ee_x"], observation["ee_y"])
        obj = _visible_object(observation)
        target = (observation["target_x"], observation["target_y"])

        if primitive in (P.STOP.value, P.SAFE_STOP.value, P.VERIFY_TARGET.value):
            self.step_idx += 1
            return _hold()

        if primitive == P.MOVE_TO_OBJECT.value:
            return self._travel(ee, obj, arrival=0.05)

        if primitive == P.REGRASP.value:
            self.step_idx += 1
            return _hold(toggle=True)

        if primitive == P.VERIFY_GRASP.value:
            if observation.get("grasped"):
                self.step_idx += 1
                return _hold()
            return _hold(toggle=True)

        if primitive == P.REALIGN.value:
            return self._travel(ee, target, arrival=0.06)

        if primitive == P.RESUME.value:
            if not observation.get("grasped"):
                return _steer(ee, obj)
            arrived = math.dist(ee, target) < 0.05
            if arrived:
                self.step_idx += 1
                return _hold(toggle=True)
            return _steer(ee, target, speed=0.05)

        self.step_idx += 1
        return _hold()

    def _travel(
        self, ee: tuple[float, float], goal: tuple[float, float], arrival: float
    ) -> dict[str, Any]:
        if math.dist(ee, goal) < arrival:
            self.step_idx += 1
        return _steer(ee, goal)


def _visible_object(observation: dict[str, Any]) -> tuple[float, float]:
    x = observation["object_x"]
    y = observation["object_y"]
    if x < 0 or y < 0:
        return FALLBACK_OBJECT
    return x, y


def _hold(toggle: bool = False) -> dict[str, Any]:
    return {"dx": 0.0, "dy": 0.0, "toggle_gripper": toggle}


def _steer(
    ee: tuple[float, float], goal: tuple[float, float], speed: float = 0.06
) -> dict[str, Any]:
    dx = goal[0] - ee[0]
    dy = goal[1] - ee[1]
    distance = math.hypot(dx, dy)
    if distance < 1e-6:
        return _hold()
    return {"dx": speed * dx / distance, "dy": speed * dy / distance, "toggle_gripper": False}
