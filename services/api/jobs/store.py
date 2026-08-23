from __future__ import annotations

import threading
from typing import Any

from core.storage.artifacts import ArtifactStore
from schemas.benchmark import BenchmarkResult, BenchmarkStatus


class JobStore:
    """Thread-safe job records with the artifact store as durable backing."""

    def __init__(self, store: ArtifactStore):
        self._store = store
        self._lock = threading.Lock()
        self._jobs: dict[str, BenchmarkResult] = {}

    def create(self, result: BenchmarkResult) -> BenchmarkResult:
        with self._lock:
            self._jobs[result.benchmark_id] = result
        self._persist(result.benchmark_id, result.model_dump())
        return result

    def update(self, benchmark_id: str, **fields: Any) -> BenchmarkResult | None:
        with self._lock:
            job = self._jobs.get(benchmark_id)
            if job is None:
                artifact = self._store.load_benchmark(benchmark_id) or {"benchmark_id": benchmark_id}
                job = BenchmarkResult.model_validate(artifact)
                self._jobs[benchmark_id] = job
            for key, value in fields.items():
                setattr(job, key, value)
            payload = job.model_dump()
        self._persist(benchmark_id, payload)
        return job

    def fail(self, benchmark_id: str, error: str) -> None:
        self.update(benchmark_id, status=BenchmarkStatus.FAILED, error=error)

    def get(self, benchmark_id: str) -> dict[str, Any] | None:
        artifact = self._store.load_benchmark(benchmark_id)
        with self._lock:
            job = self._jobs.get(benchmark_id)
        if artifact and job:
            if artifact.get("status") in ("completed", "failed"):
                return artifact
            return job.model_dump()
        if artifact:
            return artifact
        if job:
            return job.model_dump()
        return None

    def _persist(self, benchmark_id: str, payload: dict[str, Any]) -> None:
        existing = self._store.load_benchmark(benchmark_id) or {}
        merged = {**existing, **payload}
        self._store.save_benchmark(benchmark_id, merged)
