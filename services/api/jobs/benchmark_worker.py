"""Shared benchmark job execution for local threads and Modal workers."""

from __future__ import annotations

from typing import Any

from core.evaluation.suite import run_evaluation
from core.storage.artifacts import ArtifactStore
from schemas.benchmark import PROFILE_EPISODES, BenchmarkProfile, BenchmarkRequest, BenchmarkStatus
from services.api.jobs.store import JobStore

QUICK_EPISODE_CAP = 50
EPISODES_PERSISTED = 20


def execute_benchmark(
    benchmark_id: str,
    request: BenchmarkRequest,
    store: ArtifactStore,
    jobs: JobStore,
) -> dict[str, Any]:
    jobs.update(benchmark_id, status=BenchmarkStatus.RUNNING)
    requested = request.episodes or PROFILE_EPISODES[request.profile]
    total = min(requested, QUICK_EPISODE_CAP) if request.profile.value == "quick" else requested

    result = run_evaluation(
        profile=request.profile,
        episodes=total,
        policy_id=request.policy_id,
        recovery=request.recovery,
        compare_baseline=request.compare_baseline,
    )
    metrics = result["metrics"]
    job = jobs.update(
        benchmark_id,
        status=BenchmarkStatus.COMPLETED,
        progress=1.0,
        episodes_completed=len(result["episodes"]),
        metrics=metrics,
        baseline_metrics=result["baseline_metrics"],
        recovery_metrics=metrics,
        ood_metrics={"ood_recovery_success": metrics.get("ood_recovery_success", 0.0)},
    )

    payload = job.model_dump() if job else {}
    payload["episodes"] = result["episodes"]
    payload["baseline_episodes"] = result["baseline_episodes"]
    store.save_benchmark(benchmark_id, payload)

    for episode in result["episodes"][:EPISODES_PERSISTED]:
        store.save_episode(benchmark_id, episode)

    return payload


def run_benchmark_job_dict(
    benchmark_id: str,
    request_dict: dict[str, Any],
    artifacts_dir: str,
) -> dict[str, Any]:
    store = ArtifactStore(artifacts_dir)
    jobs = JobStore(store)
    request = BenchmarkRequest.model_validate(request_dict)
    return execute_benchmark(benchmark_id, request, store, jobs)
