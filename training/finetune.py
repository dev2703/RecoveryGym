"""SmolVLA fine-tune entry point.

Local runs only validate and summarise the corrective dataset. Real LoRA
training needs a Modal GPU plus HF_TOKEN; until then this reports the dataset
it would train on and never emits accuracy numbers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.dataset.corrective import read_jsonl, summarize

DEFAULT_MODEL_ID = "lerobot/smolvla_base"


def finetune_smolvla(
    dataset_path: str,
    model_id: str = DEFAULT_MODEL_ID,
    output_dir: str = "./checkpoints",
    steps: int = 500,
) -> dict[str, Any]:
    records = read_jsonl(Path(dataset_path))
    stats = summarize(records)

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "model_id": model_id,
        "steps": steps,
        "num_episodes": stats["count"],
        "dataset": stats,
        "status": "pipeline_ready" if records else "pipeline_ready_empty_dataset",
        "checkpoint": str(output / "smolvla-recovery-v1"),
        "trained": False,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
