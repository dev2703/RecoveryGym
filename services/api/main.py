from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.evaluation.suite import POLICY_FACTORIES, run_comparison
from core.scenario.engine import ScenarioEngine
from core.sim.wam_provider import WAMProvider
from core.storage.artifacts import ArtifactStore
from policies.nominal import NominalPolicy
from policies.smolvla import SmolVLAProvider
from schemas.benchmark import (
    PROFILE_EPISODES,
    BenchmarkRequest,
    BenchmarkResult,
    BenchmarkStatus,
    RunRequest,
)
from schemas.task import TaskConfig
from services.api.jobs.benchmark_worker import run_benchmark_job
from services.api.jobs.store import JobStore
from training.finetune import DEFAULT_MODEL_ID, finetune_smolvla

COMPARE_KNOWN_CAP = 20
COMPARE_OOD_CAP = 12

app = FastAPI(title="RecoveryGym API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = ArtifactStore()
engine = ScenarioEngine()
wam = WAMProvider(use_mock=True)
jobs = JobStore(store)

POLICIES: dict[str, Any] = {"nominal": NominalPolicy(), "smolvla": SmolVLAProvider()}


class PolicyRegisterRequest(BaseModel):
    policy_id: str
    model_id: str | None = None
    endpoint: str | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "recoverygym"}


@app.post("/v1/runs")
def create_run(request: RunRequest) -> dict[str, Any]:
    policy = POLICIES.get(request.policy_id, NominalPolicy())
    artifact = engine.run_episode(
        policy=policy,
        task=TaskConfig(task_id=request.task_id),
        seed=request.seed,
        failure_spec=request.failure,
        recovery=request.recovery,
    )

    counterfactual = None
    if artifact.failure_event and artifact.nominal_trajectory:
        counterfactual = wam.run_counterfactual_episode(
            {
                "steps": [s.model_dump() for s in artifact.nominal_trajectory.steps],
                "seed": request.seed,
            },
            artifact.failure_event.model_dump(),
        )
        artifact.counterfactual_available = True

    steps = artifact.perturbed_trajectory.steps if artifact.perturbed_trajectory else []
    return {
        "run_id": artifact.episode_id,
        "artifact": artifact.model_dump(),
        "counterfactual": counterfactual,
        "events": [e.model_dump() for e in artifact.events],
        "recovery_plan": artifact.expert_recovery.get("primitives", []),
        "recovery_score": artifact.recovery_score,
        "final_state": steps[-1].state if steps else {},
    }


@app.post("/v1/benchmarks")
def create_benchmark(request: BenchmarkRequest) -> dict[str, Any]:
    benchmark_id = f"bench_{uuid.uuid4().hex[:8]}"
    result = jobs.create(
        BenchmarkResult(
            benchmark_id=benchmark_id,
            status=BenchmarkStatus.QUEUED,
            profile=request.profile,
            episodes_total=request.episodes or PROFILE_EPISODES[request.profile],
            version_info={"generator": "recoverygym@0.1.0", "policy": request.policy_id},
        )
    )
    run_benchmark_job(benchmark_id=benchmark_id, request=request, store=store, jobs=jobs)
    return {"benchmark_id": benchmark_id, "status": result.status.value}


@app.get("/v1/benchmarks/{benchmark_id}")
def get_benchmark(benchmark_id: str) -> dict[str, Any]:
    data = jobs.get(benchmark_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Benchmark not found")
    return data


@app.post("/v1/policies")
def register_policy(request: PolicyRegisterRequest) -> dict[str, Any]:
    reference = (request.model_id or request.policy_id).lower()
    if "smolvla" in reference:
        POLICIES[request.policy_id] = SmolVLAProvider(model_id=request.model_id or DEFAULT_MODEL_ID)
    else:
        POLICIES[request.policy_id] = POLICY_FACTORIES.get(request.policy_id, NominalPolicy)()
    return {"policy_id": request.policy_id, "registered": True}


@app.post("/v1/datasets/{benchmark_id}/generate")
def generate_dataset(benchmark_id: str) -> dict[str, Any]:
    try:
        path = store.export_dataset_jsonl(benchmark_id)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    from core.dataset.corrective import read_jsonl, summarize

    return {
        "benchmark_id": benchmark_id,
        "dataset_path": str(path),
        "format": "jsonl",
        "summary": summarize(read_jsonl(path)),
    }


@app.post("/v1/training")
def start_training(benchmark_id: str, model_id: str = DEFAULT_MODEL_ID) -> dict[str, Any]:
    training_id = f"train_{uuid.uuid4().hex[:8]}"
    try:
        dataset_path = store.export_dataset_jsonl(benchmark_id)
    except FileNotFoundError:
        dataset_path = store.dataset_path(benchmark_id)

    pipeline = finetune_smolvla(
        dataset_path=str(dataset_path),
        model_id=model_id,
        output_dir=str(store.base_dir / training_id),
    )
    payload = {
        "training_id": training_id,
        "status": "completed_local_eval",
        "model_id": model_id,
        "benchmark_id": benchmark_id,
        "pipeline": pipeline,
        "comparison": run_comparison(known_episodes=10, ood_episodes=6, seed_base=42),
        "message": "Measured local comparison. GPU LoRA pending Modal credentials.",
    }
    store.save_benchmark(f"train_{training_id}", payload)
    return payload


@app.get("/v1/training/{training_id}")
def get_training(training_id: str) -> dict[str, Any]:
    data = store.load_benchmark(f"train_{training_id}")
    if data:
        return data
    return {
        "training_id": training_id,
        "status": "pipeline_ready",
        "checkpoint": None,
        "message": "Configure Modal GPU + HF_TOKEN to run LoRA fine-tune",
    }


@app.post("/v1/experiments/compare")
def compare_methods(known_episodes: int = 10, ood_episodes: int = 6) -> dict[str, Any]:
    return run_comparison(
        known_episodes=min(known_episodes, COMPARE_KNOWN_CAP),
        ood_episodes=min(ood_episodes, COMPARE_OOD_CAP),
        seed_base=42,
    )
