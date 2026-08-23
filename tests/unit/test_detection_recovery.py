"""Unit tests — detection, recovery, safety, scoring, splits."""

from core.detection.detector import FailureDetector
from core.evaluation.scoring import aggregate_metrics, compute_recovery_score
from core.evaluation.splits import (
    assign_scenario_split,
    is_ood_scenario,
    sample_failure_spec,
)
from core.recovery.rule_recovery import RuleRecoveryPolicy, get_recovery_plan
from core.recovery.safety import SafetyGate
from schemas.failure import FailureType
from schemas.task import TaskConfig


def _observation(**overrides):
    base = {
        "ee_x": 0.30,
        "ee_y": 0.20,
        "object_x": 0.30,
        "object_y": 0.20,
        "target_x": 0.70,
        "target_y": 0.60,
        "grasped": False,
        "gripper_open": True,
        "occlusion": False,
        "obstacle": None,
    }
    base.update(overrides)
    return base


def test_recovery_plans_for_three_families():
    for failure in (FailureType.OBJECT_SLIP, FailureType.GRASP_MISS, FailureType.TARGET_SHIFT):
        plan = get_recovery_plan(failure)
        assert len(plan) >= 3
        assert plan[-1] == "RESUME"


def test_every_failure_type_has_a_plan():
    for failure in FailureType:
        if failure is FailureType.DISTRIBUTION_SHIFT:
            continue
        assert get_recovery_plan(failure)


def test_rule_policy_advances_on_stop():
    policy = RuleRecoveryPolicy()
    plan = policy.start(FailureType.OBJECT_SLIP)
    assert plan[0] == "STOP"
    action = policy.act(_observation())
    assert action["dx"] == 0.0
    assert policy.step_idx == 1


def test_rule_policy_reports_done_once_goals_are_reached():
    policy = RuleRecoveryPolicy()
    policy.start(FailureType.TARGET_SHIFT)
    at_target = _observation(ee_x=0.70, ee_y=0.60, grasped=True)
    for _ in range(20):
        if policy.is_done():
            break
        policy.act(at_target)
    assert policy.is_done()


def test_safety_gate_clips_velocity():
    gate = SafetyGate(TaskConfig())
    action = gate.validate_action({"ee_x": 0.5, "ee_y": 0.5}, {"dx": 1.0, "dy": 1.0})
    assert abs(action["dx"]) <= 0.08
    assert abs(action["dy"]) <= 0.08


def test_safety_gate_rejects_out_of_bounds():
    gate = SafetyGate(TaskConfig())
    action = gate.validate_action({"ee_x": 0.99, "ee_y": 0.99}, {"dx": 0.08, "dy": 0.08})
    assert action["dx"] == 0.0
    assert gate.violations == 1


def test_detector_quiet_when_nothing_wrong():
    detector = FailureDetector(TaskConfig())
    observation = _observation()
    detector.observe(observation, {"dx": 0.0, "dy": 0.0, "toggle_gripper": False})
    failure, confidence, _ = detector.detect(observation)
    assert failure is None
    assert confidence == 0.0


def test_detector_flags_target_shift():
    detector = FailureDetector(TaskConfig())
    failure, confidence, _ = detector.detect(_observation(target_x=0.95, target_y=0.95))
    assert failure is FailureType.TARGET_SHIFT
    assert confidence > 0.5


def test_detector_flags_occlusion_and_obstacle():
    detector = FailureDetector(TaskConfig())
    assert detector.detect(_observation(occlusion=True))[0] is FailureType.OCCLUSION
    assert detector.detect(_observation(obstacle=(0.5, 0.4)))[0] is FailureType.OBSTACLE_APPEARS


def test_detector_flags_slip_from_predicted_grasp():
    detector = FailureDetector(TaskConfig())
    held = _observation(grasped=False)
    detector.observe(held, {"dx": 0.0, "dy": 0.0, "toggle_gripper": True})
    dropped = _observation(grasped=False, object_y=0.05)
    failure, confidence, details = detector.detect(dropped)
    assert failure is FailureType.OBJECT_SLIP
    assert confidence > 0.9
    assert details["layer"] == "invariant"


def test_detector_calls_clean_release_a_grasp_miss():
    detector = FailureDetector(TaskConfig())
    observation = _observation()
    detector.observe(observation, {"dx": 0.0, "dy": 0.0, "toggle_gripper": True})
    failure, _, _ = detector.detect(observation)
    assert failure is FailureType.GRASP_MISS


def test_recovery_score_weights_sum_to_one():
    perfect = dict.fromkeys(
        [
            "task_recovered",
            "detection_score",
            "safety_score",
            "efficiency_score",
            "latency_score",
        ],
        1.0,
    )
    assert abs(compute_recovery_score(perfect) - 1.0) < 1e-9


def test_aggregate_metrics_empty():
    assert aggregate_metrics([]) == {}


def test_ood_split_holds_out_composites_and_high_severity():
    assert is_ood_scenario(FailureType.COMPOSITE_FAILURE, 0.3, 1) is True
    assert is_ood_scenario(FailureType.OBJECT_SLIP, 0.7, 1) is True
    assert assign_scenario_split(0, FailureType.COMPOSITE_FAILURE, 0.7, 1) == "ood"


def test_sample_failure_spec_respects_split_bands():
    ood = sample_failure_spec("ood", 5)
    known = sample_failure_spec("train", 5)
    assert ood.severity >= 0.65
    assert known.severity < 0.65
    assert sample_failure_spec("train", 5).severity == known.severity
