from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from core.dataset.corrective import build_records, write_jsonl

DATASET_FILENAME = "recovery_dataset.jsonl"


class ArtifactStore:
    """Filesystem-backed store for benchmark results, episodes and datasets."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(
            base_dir or os.environ.get("RECOVERYGYM_ARTIFACTS_DIR", "./artifacts")
        )
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_benchmark(self, benchmark_id: str, data: dict[str, Any]) -> Path:
        path = self.base_dir / benchmark_id / "results.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str))
        return path

    def load_benchmark(self, benchmark_id: str) -> dict[str, Any] | None:
        path = self.base_dir / benchmark_id / "results.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def save_episode(self, benchmark_id: str, episode: dict[str, Any]) -> Path:
        path = self.base_dir / benchmark_id / "episodes"
        path.mkdir(parents=True, exist_ok=True)
        file = path / f"{episode.get('episode_id', 'unknown')}.json"
        file.write_text(json.dumps(episode, indent=2, default=str))
        return file

    def dataset_path(self, benchmark_id: str) -> Path:
        return self.base_dir / benchmark_id / DATASET_FILENAME

    def export_dataset_jsonl(self, benchmark_id: str) -> Path:
        benchmark = self.load_benchmark(benchmark_id)
        if benchmark is None:
            raise FileNotFoundError(f"Benchmark {benchmark_id} not found")
        records = build_records(benchmark.get("episodes", []))
        return write_jsonl(records, self.dataset_path(benchmark_id))

    @staticmethod
    def cache_key(*parts: Any) -> str:
        payload = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(payload.encode()).hexdigest()
