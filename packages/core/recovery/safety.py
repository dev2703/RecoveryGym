from __future__ import annotations

import math
from typing import Any

from schemas.task import TaskConfig


class SafetyGate:
    def __init__(self, task: TaskConfig):
        self.task = task
        self.violations = 0

    def reset(self) -> None:
        self.violations = 0

    def validate_action(self, state: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
        x0, x1, y0, y1 = self.task.workspace_bounds
        nx = state["ee_x"] + action.get("dx", 0.0)
        ny = state["ee_y"] + action.get("dy", 0.0)
        max_vel = 0.08
        dx = max(-max_vel, min(max_vel, action.get("dx", 0.0)))
        dy = max(-max_vel, min(max_vel, action.get("dy", 0.0)))

        if nx < x0 or nx > x1 or ny < y0 or ny > y1:
            self.violations += 1
            return {"dx": 0.0, "dy": 0.0, "toggle_gripper": action.get("toggle_gripper", False)}

        speed = math.hypot(dx, dy)
        if speed > max_vel:
            scale = max_vel / speed
            dx *= scale
            dy *= scale

        return {"dx": dx, "dy": dy, "toggle_gripper": action.get("toggle_gripper", False)}
