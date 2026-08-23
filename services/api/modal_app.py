"""Modal deployment: API, benchmark workers, and GPU fine-tuning."""

from __future__ import annotations

from pathlib import Path

try:
    import modal

    APP_NAME = "recoverygym"

    def _repo_root() -> Path:
        here = Path(__file__).resolve()
        if here.parent.name == "api":
            candidate = here.parents[2]
            if (candidate / "pyproject.toml").exists():
                return candidate
        if (here.parent / "pyproject.toml").exists():
            return here.parent
        return Path("/root")

    ROOT = _repo_root()

    app = modal.App(APP_NAME)

    image = (
        modal.Image.debian_slim(python_version="3.11")
        .apt_install("git")
        .pip_install(
            "fastapi>=0.110",
            "uvicorn[standard]>=0.27",
            "pydantic>=2.0",
            "numpy>=1.26",
            "httpx>=0.27",
            "python-dotenv>=1.0",
            "reactor-sdk",
            "huggingface_hub>=0.23",
            "datasets>=2.19",
            "torch",
            "lerobot[peft]",
        )
        .add_local_dir(str(ROOT / "packages"), remote_path="/root/packages")
        .add_local_dir(str(ROOT / "services"), remote_path="/root/services")
        .add_local_dir(str(ROOT / "training"), remote_path="/root/training")
        .add_local_file(str(ROOT / "pyproject.toml"), remote_path="/root/pyproject.toml")
        .add_local_file(str(ROOT / "requirements.txt"), remote_path="/root/requirements.txt")
    )

    secrets = modal.Secret.from_name("recoverygym-secrets")
    volume = modal.Volume.from_name("recoverygym-artifacts", create_if_missing=True)
    ARTIFACTS_MOUNT = "/data/artifacts"

    @app.function(
        image=image,
        secrets=[secrets],
        volumes={ARTIFACTS_MOUNT: volume},
        timeout=60 * 30,
    )
    def run_benchmark_job(benchmark_id: str, request_dict: dict, artifacts_dir: str) -> dict:
        import sys

        sys.path[:0] = ["/root", "/root/packages"]
        from services.api.jobs.benchmark_worker import run_benchmark_job_dict

        result = run_benchmark_job_dict(benchmark_id, request_dict, artifacts_dir)
        volume.commit()
        return result

    @app.function(
        image=image,
        secrets=[secrets],
        volumes={ARTIFACTS_MOUNT: volume},
        gpu="A10G",
        timeout=60 * 60 * 4,
    )
    def finetune_job(
        dataset_path: str,
        model_id: str,
        output_dir: str,
        steps: int,
        push_dataset: bool,
        run_training: bool,
    ) -> dict:
        import sys

        sys.path[:0] = ["/root", "/root/packages"]
        from training.finetune import finetune_smolvla

        manifest = finetune_smolvla(
            dataset_path=dataset_path,
            model_id=model_id,
            output_dir=output_dir,
            steps=steps,
            push_dataset=push_dataset,
            run_training=run_training,
        )
        volume.commit()
        return manifest

    @app.function(
        image=image,
        secrets=[secrets],
        volumes={ARTIFACTS_MOUNT: volume},
        timeout=60 * 20,
    )
    @modal.asgi_app()
    def fastapi_app():
        import os
        import sys

        sys.path[:0] = ["/root", "/root/packages"]
        os.environ.setdefault("RECOVERYGYM_ARTIFACTS_DIR", ARTIFACTS_MOUNT)
        os.environ.setdefault("USE_MODAL_JOBS", "true")
        os.environ.setdefault("MODAL_ENVIRONMENT", "1")
        os.environ.setdefault("USE_MOCK_WAM", "false")
        os.environ.setdefault("SMOLVLA_ALLOW_FALLBACK", "false")

        from services.api.main import app as fastapi_application

        return fastapi_application

except ImportError:
    app = None
