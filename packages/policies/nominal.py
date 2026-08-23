from __future__ import annotations

import math
from typing import Any

from policies.base import PolicyAdapter
from schemas.task import TaskConfig


class NominalPolicy:
    """Scripted open-loop pick-and-place policy."""

    observation_space = {"type": "dict", "keys": ["ee_x", "ee_y", "object_x", "object_y", "target_x", "target_y"]}
    action_space = {"type": "dict", "keys": ["dx", "dy", "toggle_gripper"]}

    def __init__(self):
        self.phase = "approach_object"
        self.task: TaskConfig | None = None

    def reset(self, task: TaskConfig) -> dict[str, Any]:
        self.task = task
        self.phase = "approach_object"
        return {"phase": self.phase}

    def act(self, observation: dict[str, Any], instruction: str) -> dict[str, Any]:
        ox = observation["object_x"]
        oy = observation["object_y"]
        tx = observation["target_x"]
        ty = observation["target_y"]
        ex = observation["ee_x"]
        ey = observation["ee_y"]
        grasped = observation.get("grasped", False)

        if self.phase == "approach_object" and not grasped:
            dx, dy = self._move_toward(ex, ey, ox, oy)
            if math.hypot(ex - ox, ey - oy) < 0.04:
                self.phase = "grasp"
            return {"dx": dx, "dy": dy, "toggle_gripper": False}

        if self.phase == "grasp":
            self.phase = "move_to_target"
            return {"dx": 0.0, "dy": 0.0, "toggle_gripper": True}

        if self.phase == "move_to_target" and grasped:
            dx, dy = self._move_toward(ex, ey, tx, ty)
            if math.hypot(ex - tx, ey - ty) < 0.04:
                self.phase = "place"
            return {"dx": dx, "dy": dy, "toggle_gripper": False}

        if self.phase == "place":
            self.phase = "done"
            return {"dx": 0.0, "dy": 0.0, "toggle_gripper": True}

        return {"dx": 0.0, "dy": 0.0, "toggle_gripper": False}

    def _move_toward(
        self, x: float, y: float, tx: float, ty: float, speed: float = 0.06
    ) -> tuple[float, float]:
        dx = tx - x
        dy = ty - y
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            return 0.0, 0.0
        return speed * dx / dist, speed * dy / dist

    def metadata(self) -> dict[str, Any]:
        return {"id": "nominal", "type": "scripted", "version": "1.0.0"}
