"""Reactor LingBot World 2 client for action-conditioned counterfactual video."""

from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any

import httpx
import numpy as np

from core.rendering.topdown import render_topdown
from core.sim.lingbot_prompts import (
    build_scene_prompt,
    observation_at_step,
    perturbation_actions,
)

logger = logging.getLogger(__name__)

TOKEN_URL = "https://api.reactor.inc/tokens"
DEFAULT_MODEL = "reactor/lingbot-world-2"
DEFAULT_CHUNK_WAIT_SEC = 3.0


class ReactorError(RuntimeError):
    pass


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _write_reference_image(observation: dict[str, Any]) -> Path:
    rgb = render_topdown(observation)
    path = Path(tempfile.mkstemp(suffix=".png")[1])
    try:
        from PIL import Image

        Image.fromarray(rgb).save(path)
    except ImportError as error:
        raise ReactorError("Pillow is required to upload reference images to Reactor") from error
    return path


class ReactorClient:
    """Drive LingBot World 2 for counterfactual world-model rollouts."""

    def __init__(
        self,
        api_key: str,
        model_name: str = DEFAULT_MODEL,
        chunk_wait_sec: float = DEFAULT_CHUNK_WAIT_SEC,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.chunk_wait_sec = chunk_wait_sec

    def mint_token(self) -> str:
        payload = {
            "authorization_details": [
                {
                    "type": "session",
                    "resources": {"models": {"match": [self.model_name]}},
                }
            ]
        }
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                TOKEN_URL,
                headers={
                    "Reactor-API-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("jwt") or data.get("token")
            if not token:
                raise ReactorError(f"Token response missing jwt: {data}")
            return token

    def counterfactual(
        self, trajectory: dict[str, Any], perturbation: dict[str, Any]
    ) -> dict[str, Any]:
        return _run_async(self._counterfactual_async(trajectory, perturbation))

    async def _counterfactual_async(
        self, trajectory: dict[str, Any], perturbation: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            from reactor_sdk import Reactor
        except ImportError as error:
            raise ReactorError(
                "reactor_sdk is not installed. Add reactor-sdk to requirements."
            ) from error

        step = int(perturbation.get("step", 0))
        steps = trajectory.get("steps", [])
        observation = observation_at_step(trajectory, step)
        if not observation:
            raise ReactorError("Trajectory has no observation at perturbation step")

        prompt = build_scene_prompt(observation, perturbation)
        actions = perturbation_actions(perturbation)
        if suffix := actions.pop("prompt_suffix", None):
            prompt = prompt + suffix

        seed = int(trajectory.get("seed") or perturbation.get("seed") or 42)
        image_path = _write_reference_image(observation)

        messages: list[dict[str, Any]] = []
        frames: list[dict[str, Any]] = []

        try:
            async with Reactor(model_name=self.model_name, api_key=self.api_key) as reactor:
                await reactor.connect()

                image_ready = asyncio.Event()

                @reactor.on_message
                def _on_message(msg: dict[str, Any]) -> None:
                    messages.append(msg)
                    if msg.get("type") == "image_accepted":
                        image_ready.set()

                try:
                    video = reactor.tracks.with_direction("recvonly").with_kind("video").one()

                    @video.on_frame
                    def _on_frame(frame: np.ndarray) -> None:
                        frames.append(
                            {
                                "index": len(frames),
                                "shape": list(frame.shape),
                            }
                        )
                except Exception:
                    logger.debug("Video track unavailable; relying on message events only")

                ref = await reactor.upload_file(str(image_path))
                await reactor.send_command("set_image", {"image": ref})
                try:
                    await asyncio.wait_for(image_ready.wait(), timeout=15.0)
                except asyncio.TimeoutError:
                    logger.warning("Timed out waiting for image_accepted; continuing")

                await reactor.send_command("set_seed", {"seed": seed})
                await reactor.send_command("set_prompt", {"prompt": prompt})

                for command, payload in actions.items():
                    await reactor.send_command(command, payload)

                await reactor.send_command("start", {})
                await asyncio.sleep(self.chunk_wait_sec)
                await reactor.send_command("reset", {})

        finally:
            image_path.unlink(missing_ok=True)

        cf_steps = steps[: step + 1]
        cf_steps.append(
            {
                "t": step,
                "lingbot_perturbed": True,
                "perturbation": perturbation,
                "prompt": prompt,
                "actions": actions,
                "messages": messages[:20],
            }
        )

        return {
            "nominal": steps,
            "counterfactual": cf_steps,
            "perturbation": perturbation,
            "provider": "reactor",
            "model": self.model_name,
            "prompt": prompt,
            "frames": frames[:12],
            "frame_count": len(frames),
            "events": messages[:50],
            "generation_started": any(m.get("type") == "generation_started" for m in messages),
            "chunk_complete": any(m.get("type") == "chunk_complete" for m in messages),
        }
