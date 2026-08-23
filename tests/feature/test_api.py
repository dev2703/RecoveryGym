"""Feature tests — FastAPI."""

import time

from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_run_object_slip_with_recovery():
    r = client.post(
        "/v1/runs",
        json={
            "policy_id": "nominal",
            "task_id": "pick_place_v1",
            "failure": {
                "type": "OBJECT_SLIP",
                "seed": 42,
                "time": 30.0,
                "severity": 0.5,
                "deterministic": True,
            },
            "recovery": True,
            "seed": 42,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["run_id"]
    assert data["recovery_plan"]
    assert any(e["event"] == "FAILURE_DETECTED" for e in data["events"])
    assert data["counterfactual"] is not None


def test_benchmark_completes_and_has_metrics():
    r = client.post(
        "/v1/benchmarks",
        json={"policy_id": "nominal", "profile": "quick", "episodes": 4, "recovery": True},
    )
    assert r.status_code == 200
    bid = r.json()["benchmark_id"]

    final = None
    for _ in range(40):
        final = client.get(f"/v1/benchmarks/{bid}").json()
        if final["status"] in ("completed", "failed"):
            break
        time.sleep(0.15)

    assert final is not None
    assert final["status"] == "completed"
    assert "metrics" in final
    assert final["episodes_completed"] >= 1


def test_dataset_generate_after_benchmark():
    r = client.post(
        "/v1/benchmarks",
        json={"policy_id": "nominal", "profile": "quick", "episodes": 3},
    )
    bid = r.json()["benchmark_id"]
    for _ in range(40):
        status = client.get(f"/v1/benchmarks/{bid}").json()
        if status["status"] in ("completed", "failed"):
            break
        time.sleep(0.15)

    ds = client.post(f"/v1/datasets/{bid}/generate")
    assert ds.status_code == 200
    assert ds.json()["format"] == "jsonl"


def test_register_policy():
    r = client.post("/v1/policies", json={"policy_id": "custom_a", "model_id": "nominal"})
    assert r.status_code == 200
    assert r.json()["registered"] is True


def test_compare_endpoint():
    r = client.post("/v1/experiments/compare?known_episodes=3&ood_episodes=2")
    assert r.status_code == 200
    data = r.json()
    assert "summary_table" in data
    assert len(data["summary_table"]) == 4
