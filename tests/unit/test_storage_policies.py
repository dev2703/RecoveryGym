"""Unit tests — storage, corrective dataset, policy adapters."""

from core.dataset.corrective import build_records, summarize
from core.storage.artifacts import ArtifactStore
from policies.nominal import NominalPolicy
from policies.smolvla import SmolVLAProvider, SmolVLARecovery
from schemas.failure import FailureType
from schemas.task import TaskConfig


def _episode(episode_id="ep1", with_failure=True, is_ood=False):
    return {
        "episode_id": episode_id,
        "task_id": "pick_place_v1",
        "seed": 1,
        "failure_event": {"type": "OBJECT_SLIP", "severity": 0.4} if with_failure else None,
        "expert_recovery": {
            "primitives": ["STOP", "MOVE_TO_OBJECT", "REGRASP"],
            "trajectory": [
                {"observation": {"ee_x": 0.1}, "action": {"dx": 0.05, "dy": 0.0}},
                {"observation": {"ee_x": 0.15}, "action": {"dx": 0.05, "dy": 0.0}},
            ],
        },
        "outcome": "SUCCESS",
        "recovery_score": 0.8,
        "is_ood": is_ood,
    }


def test_artifact_store_roundtrip(tmp_path):
    store = ArtifactStore(str(tmp_path))
    store.save_benchmark("b1", {"benchmark_id": "b1", "status": "completed", "episodes": []})
    assert store.load_benchmark("b1")["benchmark_id"] == "b1"


def test_load_missing_benchmark_returns_none(tmp_path):
    assert ArtifactStore(str(tmp_path)).load_benchmark("nope") is None


def test_dataset_export_writes_action_chunks(tmp_path):
    store = ArtifactStore(str(tmp_path))
    store.save_benchmark("b2", {"episodes": [_episode()]})
    path = store.export_dataset_jsonl("b2")
    assert path.exists()
    body = path.read_text()
    assert "OBJECT_SLIP" in body
    assert "actions" in body


def test_build_records_skips_episodes_without_failure():
    records = build_records([_episode(with_failure=False), _episode()])
    assert len(records) == 1
    assert records[0]["actions"]


def test_summarize_counts_ood_and_chunks():
    stats = summarize(build_records([_episode("a"), _episode("b", is_ood=True)]))
    assert stats["count"] == 2
    assert stats["ood"] == 1
    assert stats["with_action_chunks"] == 2
    assert stats["by_failure_type"]["OBJECT_SLIP"] == 2


def test_cache_key_stable():
    first = ArtifactStore.cache_key("a", 1, {"x": 2})
    assert first == ArtifactStore.cache_key("a", 1, {"x": 2})
    assert first != ArtifactStore.cache_key("a", 2, {"x": 2})


def test_policy_metadata():
    assert NominalPolicy().metadata()["id"] == "nominal"
    assert SmolVLAProvider().metadata()["id"] == "smolvla"
    assert SmolVLAProvider(fine_tuned=True).metadata()["fine_tuned"] is True


def test_smolvla_normalizes_actions():
    policy = SmolVLAProvider()
    policy.reset(TaskConfig())
    action = policy.act(
        {
            "ee_x": 0.1,
            "ee_y": 0.1,
            "object_x": 0.3,
            "object_y": 0.2,
            "target_x": 0.7,
            "target_y": 0.6,
            "grasped": False,
            "gripper_open": True,
        },
        "pick and place",
    )
    assert {"dx", "dy", "toggle_gripper"} <= set(action)
    assert action["source"] in ("smolvla_zeroshot", "smolvla_fallback")


def test_smolvla_recovery_is_a_recovery_adapter():
    recovery = SmolVLARecovery()
    plan = recovery.start(FailureType.OBJECT_SLIP)
    assert plan[0] == "STOP"
    assert recovery.name == "SMOLVLA_RECOVERY"
    action = recovery.act(
        {
            "ee_x": 0.1,
            "ee_y": 0.1,
            "object_x": 0.3,
            "object_y": 0.2,
            "target_x": 0.7,
            "target_y": 0.6,
            "grasped": False,
        }
    )
    assert action["source"] == "smolvla_recovery"
