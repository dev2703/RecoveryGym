from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

CHUNK_LIMIT = 16


def build_records(episodes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Turn episode artifacts into corrective training records.

    One record per episode that actually carried a perturbation, holding the
    observation/action chunk the recovery policy produced plus the primitive
    sequence as supervision metadata.
    """
    records: list[dict[str, Any]] = []
    for episode in episodes:
        failure = episode.get("failure_event")
        if not failure:
            continue
        recovery = episode.get("expert_recovery") or {}
        steps = recovery.get("trajectory") or []
        records.append(
            {
                "episode_id": episode.get("episode_id"),
                "task_id": episode.get("task_id"),
                "seed": episode.get("seed"),
                "failure_type": failure.get("type"),
                "severity": failure.get("severity"),
                "primitives": recovery.get("primitives", []),
                "observations": [s.get("observation", {}) for s in steps[:CHUNK_LIMIT]],
                "actions": [s.get("action", {}) for s in steps[:CHUNK_LIMIT]],
                "outcome": episode.get("outcome"),
                "recovery_score": episode.get("recovery_score"),
                "is_ood": episode.get("is_ood", False),
            }
        )
    return records


def write_jsonl(records: list[dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as handle:
        for record in records:
            handle.write(json.dumps(record, default=str) + "\n")
    return path


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_failure: dict[str, int] = {}
    with_actions = 0
    for record in records:
        key = str(record.get("failure_type"))
        by_failure[key] = by_failure.get(key, 0) + 1
        if record.get("actions"):
            with_actions += 1
    return {
        "count": len(records),
        "with_action_chunks": with_actions,
        "ood": sum(1 for r in records if r.get("is_ood")),
        "by_failure_type": by_failure,
    }
