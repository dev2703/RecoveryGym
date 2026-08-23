"""Unit tests for LingBot prompt and action mapping."""

from core.sim.lingbot_prompts import build_scene_prompt, perturbation_actions


def test_build_scene_prompt_mentions_failure():
    prompt = build_scene_prompt(
        {"grasped": True, "object_x": 0.3, "object_y": 0.2},
        {"type": "OBJECT_SLIP", "severity": 0.6},
    )
    assert "object slip" in prompt.lower()
    assert "holding" in prompt.lower()


def test_object_slip_maps_to_lateral_motion():
    actions = perturbation_actions({"type": "OBJECT_SLIP", "severity": 0.7})
    assert actions["set_move_lateral"]["move_lateral"] == "strafe_right"


def test_target_shift_updates_prompt_suffix():
    actions = perturbation_actions({"type": "TARGET_SHIFT", "severity": 0.4})
    assert "prompt_suffix" in actions


def test_actuator_deviation_sets_camera_pose():
    actions = perturbation_actions({"type": "ACTUATOR_DEVIATION", "severity": 0.5})
    assert "set_camera_pose" in actions
    assert len(actions["set_camera_pose"]["camera_pose"]) == 6
