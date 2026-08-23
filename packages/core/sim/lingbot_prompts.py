"""Prompt and action mapping for LingBot World 2 counterfactual rollouts."""

from __future__ import annotations

from typing import Any


def observation_at_step(trajectory: dict[str, Any], step: int) -> dict[str, Any]:
    steps = trajectory.get("steps", [])
    if not steps:
        return {}
    idx = min(max(step, 0), len(steps) - 1)
    obs = steps[idx].get("observation") or steps[idx].get("state") or {}
    return dict(obs)


def build_scene_prompt(observation: dict[str, Any], perturbation: dict[str, Any]) -> str:
    failure = perturbation.get("type", "UNKNOWN")
    severity = float(perturbation.get("severity") or 0.5)
    grasped = observation.get("grasped", False)
    return (
        "Top-down view of a robot pick-and-place workspace. "
        "A gray robot arm, a red cube object, and a blue target tray on a light table. "
        "The camera is fixed above the scene looking down. "
        f"The robot is {'holding the cube' if grasped else 'approaching the cube'}. "
        f"A {failure.replace('_', ' ').lower()} failure occurs with severity {severity:.2f}. "
        "The cube and arm remain physically consistent; only the described failure disturbs the scene."
    )


def perturbation_actions(perturbation: dict[str, Any]) -> dict[str, Any]:
    """Map RecoveryGym failure events to LingBot World 2 commands."""
    failure = str(perturbation.get("type", ""))
    severity = float(perturbation.get("severity") or 0.5)
    magnitude = min(0.12, 0.03 + severity * 0.08)

    actions: dict[str, Any] = {}

    if failure == "OBJECT_SLIP":
        actions["set_move_lateral"] = {"move_lateral": "strafe_right" if severity > 0.5 else "strafe_left"}
        actions["set_move_longitudinal"] = {"move_longitudinal": "back"}
    elif failure == "TARGET_SHIFT":
        actions["prompt_suffix"] = " The target tray shifts slightly away from the robot."
    elif failure == "ACTUATOR_DEVIATION":
        actions["set_camera_pose"] = {"camera_pose": [0, 0, magnitude, magnitude, -magnitude, 0]}
    elif failure == "SENSOR_NOISE":
        actions["set_camera_pose"] = {"camera_pose": [magnitude, 0, 0, 0, 0, 0]}
    elif failure == "OCCLUSION":
        actions["prompt_suffix"] = " A brief shadow occludes part of the workspace."
    elif failure == "OBSTACLE_APPEARS":
        actions["prompt_suffix"] = " A new obstacle appears between the arm and the target."
    elif failure == "GRASP_MISS":
        actions["set_move_longitudinal"] = {"move_longitudinal": "forward"}
    elif failure == "COMPOSITE_FAILURE":
        actions["set_camera_pose"] = {"camera_pose": [0, magnitude, 0, -magnitude, magnitude, 0]}
        actions["prompt_suffix"] = " Multiple disturbances hit the scene at once."
    else:
        actions["set_camera_pose"] = {"camera_pose": [0, magnitude, 0, 0, -magnitude, 0]}

    return actions
