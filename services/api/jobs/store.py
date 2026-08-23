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
        return result

    def update(self, benchmark_id: str, **fields: Any) -> BenchmarkResult | None:
        with self._lock:
            job = self._jobs.get(benchmark_id)
            if job is None:
                return None
            for key, value in fields.items():
                setattr(job, key, value)
            return job

    def fail(self, benchmark_id: str, error: str) -> None:
        self.update(benchmark_id, status=BenchmarkStatus.FAILED, error=error)

    def get(self, benchmark_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(benchmark_id)
        if job is not None:
            return job.model_dump()
        return self._store.load_benchmark(benchmark_id)
