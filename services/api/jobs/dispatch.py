"""Dispatch benchmark jobs locally or via Modal."""

from __future__ import annotations

import threading
from typing import Any

from core.config import get_settings
from schemas.benchmark import BenchmarkRequest
from services.api.jobs.benchmark_worker import execute_benchmark


def dispatch_benchmark_job(
    benchmark_id: str,
    request: BenchmarkRequest,
    store: Any,
    jobs: Any,
) -> None:
    settings = get_settings()

    if settings.use_modal_jobs:
        try:
            import modal

            fn = modal.Function.from_name("recoverygym", "run_benchmark_job")
            fn.spawn(
                benchmark_id,
                request.model_dump(mode="json"),
                settings.artifacts_dir,
            )
            return
        except Exception:
            pass

    def worker() -> None:
        try:
            execute_benchmark(benchmark_id, request, store, jobs)
        except Exception as error:
            jobs.fail(benchmark_id, str(error))

    threading.Thread(target=worker, daemon=True).start()
