"""Feature tests — end-to-end scenario engine."""

from core.scenario.engine import ScenarioEngine
from schemas.failure import FailureSpec, FailureType


def test_episode_emits_failure_and_recovery_events():
    engine = ScenarioEngine()
    spec = FailureSpec(
        type=FailureType.OBJECT_SLIP,
        seed=42,
        time=28.0,
        severity=0.5,
        deterministic=True,
    )
    artifact = engine.run_episode(seed=42, failure_spec=spec, recovery=True)
    names = [e.event for e in artifact.events]
    assert "FAILURE_INJECTED" in names
    assert "FAILURE_DETECTED" in names
    assert "RECOVERY_STARTED" in names
    assert "RECOVERY_VERIFIED" in names
    assert artifact.expert_recovery["primitives"]


def test_three_families_detect_and_start_recovery():
    engine = ScenarioEngine()
    cases = [
        (FailureType.OBJECT_SLIP, 42, 28.0),
        (FailureType.GRASP_MISS, 7, 22.0),
        (FailureType.TARGET_SHIFT, 11, 40.0),
    ]
    for ftype, seed, t in cases:
        spec = FailureSpec(type=ftype, seed=seed, time=t, severity=0.5, deterministic=True)
        artifact = engine.run_episode(seed=seed, failure_spec=spec, recovery=True)
        events = {e.event for e in artifact.events}
        assert "FAILURE_DETECTED" in events, ftype
        assert "RECOVERY_STARTED" in events, ftype
        assert artifact.metrics["detection_score"] == 1.0


def test_same_seed_same_failure_type():
    engine = ScenarioEngine()
    spec = FailureSpec(
        type=FailureType.GRASP_MISS,
        seed=9,
        time=20.0,
        severity=0.5,
        deterministic=True,
    )
    a = engine.run_episode(seed=9, failure_spec=spec, recovery=True)
    b = engine.run_episode(seed=9, failure_spec=spec, recovery=True)
    assert a.failure_event.type == b.failure_event.type
    assert a.failure_event.severity == b.failure_event.severity


def test_without_recovery_still_records_injection():
    engine = ScenarioEngine()
    spec = FailureSpec(
        type=FailureType.OBJECT_SLIP,
        seed=3,
        time=25.0,
        severity=0.6,
        deterministic=True,
    )
    artifact = engine.run_episode(seed=3, failure_spec=spec, recovery=False)
    assert any(e.event == "FAILURE_INJECTED" for e in artifact.events)
    assert not any(e.event == "RECOVERY_STARTED" for e in artifact.events)
