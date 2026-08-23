"""Render a simple top-down RGB frame from pick-and-place observations."""

from __future__ import annotations

from typing import Any

import numpy as np

CANVAS = 224
WORLD_MAX = 1.0


def render_topdown(observation: dict[str, Any]) -> np.ndarray:
    """Return HWC uint8 RGB image for VLA policies."""
    img = np.ones((CANVAS, CANVAS, 3), dtype=np.uint8) * 245

    def to_px(x: float, y: float) -> tuple[int, int]:
        px = int(np.clip(x / WORLD_MAX, 0.0, 1.0) * (CANVAS - 1))
        py = int(np.clip(1.0 - y / WORLD_MAX, 0.0, 1.0) * (CANVAS - 1))
        return px, py

    tx, ty = to_px(observation["target_x"], observation["target_y"])
    _draw_square(img, tx, ty, 14, (70, 130, 255))

    ox, oy = to_px(observation["object_x"], observation["object_y"])
    _draw_square(img, ox, oy, 10, (220, 80, 60))

    ex, ey = to_px(observation["ee_x"], observation["ee_y"])
    _draw_circle(img, ex, ey, 8, (40, 40, 40))

    if observation.get("obstacle") is not None:
        bx, by = observation["obstacle"]
        bx_px, by_px = to_px(bx, by)
        _draw_square(img, bx_px, by_px, 12, (120, 120, 120))

    return img


def _draw_square(img: np.ndarray, x: int, y: int, half: int, color: tuple[int, int, int]) -> None:
    x0, x1 = max(0, x - half), min(CANVAS, x + half)
    y0, y1 = max(0, y - half), min(CANVAS, y + half)
    img[y0:y1, x0:x1] = color


def _draw_circle(img: np.ndarray, x: int, y: int, radius: int, color: tuple[int, int, int]) -> None:
    y_grid, x_grid = np.ogrid[:CANVAS, :CANVAS]
    mask = (x_grid - x) ** 2 + (y_grid - y) ** 2 <= radius**2
    img[mask] = color
