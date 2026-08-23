from __future__ import annotations

import math
from typing import Any

from schemas.task import TaskConfig


class PickPlaceEnv:
    """Pure-Python 2D kinematic pick-and-place environment."""

    def __init__(self, task: TaskConfig, seed: int = 0):
        self.task = task
        self.seed = seed
        self.t = 0
        self.state: dict[str, Any] = {}
        self.sensor_noise: tuple[float, float] = (0.0, 0.0)
        self.actuator_bias: tuple[float, float] = (0.0, 0.0)
        self.occlusion = False
        self.obstacle: tuple[float, float] | None = None
        self.target_shift: tuple[float, float] = (0.0, 0.0)
        self.friction = 1.0
        self.reset(seed)

    def reset(self, seed: int | None = None) -> dict[str, Any]:
        if seed is not None:
            self.seed = seed
        self.t = 0
        ox, oy = self.task.object_position
        tx, ty = self.task.target_position
        self.state = {
            "ee_x": 0.1,
            "ee_y": 0.1,
            "gripper_open": True,
            "grasped": False,
            "object_x": ox,
            "object_y": oy,
            "target_x": tx,
            "target_y": ty,
            "object_stable": True,
            "robot_safe": True,
        }
        self.sensor_noise = (0.0, 0.0)
        self.actuator_bias = (0.0, 0.0)
        self.occlusion = False
        self.obstacle = None
        self.target_shift = (0.0, 0.0)
        self.friction = 1.0
        return self.get_observation()

    def get_observation(self) -> dict[str, Any]:
        s = self.state
        noise_x, noise_y = self.sensor_noise
        obs = {
            "ee_x": s["ee_x"] + noise_x,
            "ee_y": s["ee_y"] + noise_y,
            "gripper_open": s["gripper_open"],
            "grasped": s["grasped"],
            "object_x": s["object_x"] + noise_x * 0.5,
            "object_y": s["object_y"] + noise_y * 0.5,
            "target_x": s["target_x"] + self.target_shift[0],
            "target_y": s["target_y"] + self.target_shift[1],
            "occlusion": self.occlusion,
            "obstacle": self.obstacle,
            "t": self.t,
        }
        if self.occlusion:
            obs["object_x"] = -1.0
            obs["object_y"] = -1.0
        return obs

    def step(self, action: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        s = self.state
        dx = action.get("dx", 0.0) + self.actuator_bias[0]
        dy = action.get("dy", 0.0) + self.actuator_bias[1]
        max_vel = 0.08
        dx = max(-max_vel, min(max_vel, dx))
        dy = max(-max_vel, min(max_vel, dy))

        s["ee_x"] = max(0.0, min(1.0, s["ee_x"] + dx))
        s["ee_y"] = max(0.0, min(1.0, s["ee_y"] + dy))

        if action.get("toggle_gripper"):
            s["gripper_open"] = not s["gripper_open"]
            if not s["gripper_open"]:
                dist = math.hypot(s["ee_x"] - s["object_x"], s["ee_y"] - s["object_y"])
                tol = self.task.tolerance["grasp_distance"]
                if dist <= tol:
                    s["grasped"] = True
                else:
                    s["gripper_open"] = True
            else:
                s["grasped"] = False

        if s["grasped"]:
            s["object_x"] = s["ee_x"]
            s["object_y"] = s["ee_y"]

        self.t += 1
        done = self.is_success() or self.t >= self.task.max_steps
        return self.get_observation(), done

    def force_slip(self, severity: float, direction: str = "negative_y") -> None:
        if not self.state["grasped"]:
            return
        self.state["grasped"] = False
        self.state["gripper_open"] = True
        offset = severity * 0.15
        if direction == "negative_y":
            self.state["object_y"] -= offset
        elif direction == "positive_y":
            self.state["object_y"] += offset
        elif direction == "negative_x":
            self.state["object_x"] -= offset
        else:
            self.state["object_x"] += offset

    def force_grasp_miss(self) -> None:
        self.state["grasped"] = False
        self.state["gripper_open"] = True

    def shift_target(self, severity: float) -> None:
        self.target_shift = (severity * 0.12, severity * 0.08)
        self.state["target_x"] = self.task.target_position[0] + self.target_shift[0]
        self.state["target_y"] = self.task.target_position[1] + self.target_shift[1]

    def is_success(self) -> bool:
        s = self.state
        tx = s["target_x"]
        ty = s["target_y"]
        dist = math.hypot(s["object_x"] - tx, s["object_y"] - ty)
        return (
            dist <= self.task.tolerance["target_radius"]
            and not s["grasped"]
            and s["object_stable"]
            and s["robot_safe"]
        )

    def snapshot(self) -> dict[str, Any]:
        return dict(self.state)
