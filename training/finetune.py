"""SmolVLA fine-tune entry point with optional Modal GPU execution."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from core.config import get_settings
from core.dataset.corrective import read_jsonl, summarize
from training.export.lerobot import export_jsonl, push_to_hub

DEFAULT_MODEL_ID = "lerobot/smolvla_base"


def _write_manifest(
    output: Path,
    *,
    model_id: str,
    steps: int,
    stats: dict[str, Any],
    trained: bool,
    checkpoint: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = {
        "model_id": model_id,
        "steps": steps,
        "num_episodes": stats.get("count", 0),
        "dataset": stats,
        "status": "trained" if trained else "pipeline_ready",
        "checkpoint": checkpoint,
        "trained": trained,
    }
    if extra:
        manifest.update(extra)
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def finetune_smolvla(
    dataset_path: str,
    model_id: str = DEFAULT_MODEL_ID,
    output_dir: str = "./checkpoints",
    steps: int = 500,
    push_dataset: bool = False,
    run_training: bool | None = None,
) -> dict[str, Any]:
    cfg = get_settings()
    records = read_jsonl(Path(dataset_path))
    stats = summarize(records)
    output = Path(output_dir)
    export_dir = output / "lerobot"
    export_jsonl(records, export_dir)

    hf_upload = None
    if push_dataset and records:
        hf_upload = push_to_hub(dataset_path)

    should_train = run_training
    if should_train is None:
        should_train = bool(cfg.hf_token) and not cfg.smolvla_allow_fallback

    checkpoint = str(output / "smolvla-recovery-v1")
    if not should_train or not records:
        status = "pipeline_ready_empty_dataset" if not records else "pipeline_ready"
        manifest = _write_manifest(
            output,
            model_id=model_id,
            steps=steps,
            stats=stats,
            trained=False,
            checkpoint=checkpoint,
            extra={"hf_upload": hf_upload, "lerobot_export": str(export_dir / "lerobot_export.jsonl")},
        )
        manifest["status"] = status
        return manifest

    repo_id = cfg.hf_model_repo or f"{_hf_user(cfg)}/recoverygym-smolvla-recovery"
    dataset_repo = cfg.hf_dataset_repo
    if not dataset_repo and hf_upload:
        dataset_repo = hf_upload["repo_id"]

    if cfg.hf_token:
        os.environ.setdefault("HF_TOKEN", cfg.hf_token)
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", cfg.hf_token)

    if dataset_repo and push_dataset is False:
        export_path = export_dir / "lerobot_export.jsonl"
        try:
            hf_upload = push_to_hub(export_path, repo_id=dataset_repo)
            dataset_repo = hf_upload["repo_id"]
        except Exception:
            dataset_repo = None

    if not dataset_repo:
        return _write_manifest(
            output,
            model_id=model_id,
            steps=steps,
            stats=stats,
            trained=False,
            checkpoint=checkpoint,
            extra={
                "error": "Set HF_DATASET_REPO or push_dataset=true before training",
                "hf_upload": hf_upload,
            },
        )

    cmd = [
        sys.executable,
        "-m",
        "lerobot.scripts.train",
        f"--policy.path={model_id}",
        f"--policy.repo_id={repo_id}",
        f"--dataset.repo_id={dataset_repo}",
        f"--output_dir={checkpoint}",
        f"--steps={steps}",
        "--batch_size=4",
        "--policy.device=cuda",
        "--peft.method_type=LORA",
        "--peft.r=64",
        "--peft.lora_alpha=64",
        "--policy.optimizer_lr=1e-3",
        "--wandb.enable=false",
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        trained = True
        train_log = "completed"
    except FileNotFoundError:
        cmd[2] = "lerobot_train"
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            trained = True
            train_log = "completed"
        except Exception as error:
            trained = False
            train_log = str(error)
    except subprocess.CalledProcessError as error:
        trained = False
        train_log = error.stderr or error.stdout or str(error)

    return _write_manifest(
        output,
        model_id=model_id,
        steps=steps,
        stats=stats,
        trained=trained,
        checkpoint=checkpoint,
        extra={
            "hf_upload": hf_upload,
            "dataset_repo": dataset_repo,
            "model_repo": repo_id,
            "train_log": train_log,
        },
    )


def _hf_user(cfg) -> str:
    if not cfg.hf_token:
        return "recoverygym"
    try:
        from huggingface_hub import HfApi

        return HfApi(token=cfg.hf_token).whoami()["name"]
    except Exception:
        return "recoverygym"
