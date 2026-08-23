"""Export RecoveryGym corrective records to Hugging Face Hub."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.config import get_settings
from core.dataset.corrective import read_jsonl


def to_lerobot_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in records:
        for idx, (obs, action) in enumerate(
            zip(record.get("observations", []), record.get("actions", []), strict=False)
        ):
            rows.append(
                {
                    "episode_id": record.get("episode_id"),
                    "frame_index": idx,
                    "task": record.get("task_id", "pick_place_v1"),
                    "instruction": "Recover from failure and complete pick-and-place.",
                    "failure_type": record.get("failure_type"),
                    "severity": record.get("severity"),
                    "observation.state.ee_x": obs.get("ee_x"),
                    "observation.state.ee_y": obs.get("ee_y"),
                    "observation.state.object_x": obs.get("object_x"),
                    "observation.state.object_y": obs.get("object_y"),
                    "observation.state.target_x": obs.get("target_x"),
                    "observation.state.target_y": obs.get("target_y"),
                    "action.dx": action.get("dx"),
                    "action.dy": action.get("dy"),
                    "action.toggle_gripper": action.get("toggle_gripper"),
                    "primitives": json.dumps(record.get("primitives", [])),
                    "outcome": record.get("outcome"),
                    "is_ood": record.get("is_ood", False),
                }
            )
    return rows


def export_jsonl(records: list[dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "lerobot_export.jsonl"
    rows = to_lerobot_rows(records)
    with path.open("w") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str) + "\n")
    return path


def push_to_hub(
    dataset_path: str | Path,
    repo_id: str | None = None,
    private: bool = True,
) -> dict[str, Any]:
    cfg = get_settings()
    token = cfg.hf_token
    if not token:
        raise RuntimeError("HF_TOKEN is required to push datasets")

    repo = repo_id or cfg.hf_dataset_repo
    if not repo:
        raise RuntimeError("HF_DATASET_REPO is required")

    records = read_jsonl(Path(dataset_path))
    rows = to_lerobot_rows(records)
    if not rows:
        raise RuntimeError("No rows to upload")

    try:
        from datasets import Dataset
    except ImportError as error:
        raise RuntimeError("Install datasets and huggingface_hub for HF export") from error

    dataset = Dataset.from_list(rows)
    dataset.push_to_hub(repo, token=token, private=private)
    return {
        "repo_id": repo,
        "rows": len(rows),
        "url": f"https://huggingface.co/datasets/{repo}",
    }
