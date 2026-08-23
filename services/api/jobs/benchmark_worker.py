from __future__ import annotations

import threading

from core.evaluation.suite import run_evaluation
from core.storage.artifacts import ArtifactStore
from schemas.benchmark import PROFILE_EPISODES, BenchmarkRequest, BenchmarkStatus
from services.api.jobs.store import JobStore

# Keeps the interactive demo responsive; batch profiles run their full count.
QUICK_EPISODE_CAP = 50
EPISODES_PERSISTED = 20


def run_benchmark_job(
    benchmark_id: str,
    request: BenchmarkRequest,
    store: ArtifactStore,
    jobs: JobStore,
) -> None:
    def worker() -> None:
        jobs.update(benchmark_id, status=BenchmarkStatus.RUNNING)
        requested = request.episodes or PROFILE_EPISODES[request.profile]
        total = min(requested, QUICK_EPISODE_CAP) if request.profile.value == "quick" else requested

        try:
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

        except Exception as error:  # surfaced to the client via job status
            jobs.fail(benchmark_id, str(error))

    threading.Thread(target=worker, daemon=True).start()
