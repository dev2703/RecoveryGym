"""Unit tests — failure generators."""

from core.failures.generators import (
    GENERATOR_REGISTRY,
    apply_failure,
    sample_failure,
)
from core.simulator.pick_place import PickPlaceEnv
from schemas.failure import FailureSpec, FailureType
from schemas.task import TaskConfig


def test_all_eight_generators_registered():
    expected = {
        FailureType.GRASP_MISS,
        FailureType.OBJECT_SLIP,
        FailureType.TARGET_SHIFT,
        FailureType.ACTUATOR_DEVIATION,
        FailureType.SENSOR_NOISE,
        FailureType.OCCLUSION,
        FailureType.OBSTACLE_APPEARS,
        FailureType.COMPOSITE_FAILURE,
    }
    assert set(GENERATOR_REGISTRY.keys()) == expected


def test_deterministic_object_slip_reproduces():
    task = TaskConfig()
    spec = FailureSpec(
        type=FailureType.OBJECT_SLIP,
        seed=42,
        time=30.0,
        severity=0.5,
        deterministic=True,
        parameters={"direction": "negative_y"},
    )
    e1 = sample_failure(FailureType.OBJECT_SLIP, 42, task, spec)
    e2 = sample_failure(FailureType.OBJECT_SLIP, 42, task, spec)
    assert e1.severity == e2.severity
    assert e1.direction == e2.direction
    assert e1.step == e2.step


def test_stochastic_varies_across_seeds():
    task = TaskConfig()
    events = [sample_failure(FailureType.OBJECT_SLIP, s, task, None) for s in (1, 2, 3, 99, 100)]
    params = {(e.severity, e.direction, e.step) for e in events}
    assert len(params) > 1


def test_apply_target_shift_changes_target():
    env = PickPlaceEnv(TaskConfig(), seed=0)
    event = sample_failure(
        FailureType.TARGET_SHIFT,
        7,
        TaskConfig(),
        FailureSpec(type=FailureType.TARGET_SHIFT, seed=7, severity=0.8, time=10.0, deterministic=True),
    )
    before = (env.state["target_x"], env.state["target_y"])
    apply_failure(env, event)
    after = (env.state["target_x"], env.state["target_y"])
    assert before != after


def test_composite_has_components():
    task = TaskConfig()
    event = sample_failure(FailureType.COMPOSITE_FAILURE, 5, task, None)
    assert event.type == FailureType.COMPOSITE_FAILURE
    assert len(event.components) >= 2
