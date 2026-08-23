"""Central configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        env_path = Path(".env")
        if not env_path.exists():
            return
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    reactor_api_key: str | None
    hf_token: str | None
    artifacts_dir: str
    use_mock_wam: bool
    reactor_model_name: str
    reactor_chunk_wait_sec: float
    smolvla_model_id: str
    smolvla_checkpoint: str | None
    smolvla_allow_fallback: bool
    smolvla_device: str
    use_modal_jobs: bool
    hf_dataset_repo: str | None
    hf_model_repo: str | None
    cors_origins: list[str]

    @classmethod
    def from_env(cls) -> Settings:
        _load_dotenv()
        has_reactor = bool(os.environ.get("REACTOR_API_KEY"))
        has_hf = bool(os.environ.get("HF_TOKEN"))
        cors_raw = os.environ.get("CORS_ORIGINS", "*")
        return cls(
            reactor_api_key=os.environ.get("REACTOR_API_KEY"),
            hf_token=os.environ.get("HF_TOKEN"),
            artifacts_dir=os.environ.get("RECOVERYGYM_ARTIFACTS_DIR", "./artifacts"),
            use_mock_wam=_bool("USE_MOCK_WAM", default=not has_reactor),
            reactor_model_name=os.environ.get(
                "REACTOR_MODEL_NAME", "reactor/lingbot-world-2"
            ),
            reactor_chunk_wait_sec=float(os.environ.get("REACTOR_CHUNK_WAIT_SEC", "3.0")),
            smolvla_model_id=os.environ.get("SMOLVLA_MODEL_ID", "lerobot/smolvla_base"),
            smolvla_checkpoint=os.environ.get("SMOLVLA_CHECKPOINT"),
            smolvla_allow_fallback=_bool("SMOLVLA_ALLOW_FALLBACK", default=not has_hf),
            smolvla_device=os.environ.get("SMOLVLA_DEVICE", "auto"),
            use_modal_jobs=_bool("USE_MODAL_JOBS", default=_bool("MODAL_ENVIRONMENT")),
            hf_dataset_repo=os.environ.get("HF_DATASET_REPO"),
            hf_model_repo=os.environ.get("HF_MODEL_REPO"),
            cors_origins=[o.strip() for o in cors_raw.split(",") if o.strip()],
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
