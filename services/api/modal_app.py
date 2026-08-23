"""Modal deployment entry point."""

from __future__ import annotations

try:
    import modal

    app = modal.App("recoverygym")

    image = modal.Image.debian_slim(python_version="3.11").pip_install(
        "fastapi", "uvicorn", "pydantic", "numpy", "httpx"
    )

    @app.function(image=image)
    @modal.asgi_app()
    def fastapi_app():
        from services.api.main import app as fastapi_application

        return fastapi_application

except ImportError:
    app = None
