"""Reactor.inc client for world-model counterfactual rollouts."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

TOKEN_URL = "https://api.reactor.inc/tokens"


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


class ReactorClient:
    """Mint session tokens and drive a Reactor-hosted world model."""

    def __init__(
        self,
        api_key: str,
        model_name: str,
        counterfactual_command: str = "counterfactual_rollout",
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.counterfactual_command = counterfactual_command

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

        steps = trajectory.get("steps", [])
        summary = {
            "seed": trajectory.get("seed"),
            "num_steps": len(steps),
            "final_state": steps[-1].get("state") if steps else {},
            "perturbation": perturbation,
        }
        prompt = (
            "RecoveryGym counterfactual rollout. "
            f"Context: {json.dumps(summary, default=str)[:4000]}"
        )

        events: list[dict[str, Any]] = []
        async with Reactor(model_name=self.model_name, api_key=self.api_key) as reactor:
            await reactor.connect()
            await reactor.send_command("set_prompt", {"prompt": prompt})
            await reactor.send_command(
                self.counterfactual_command,
                {
                    "trajectory": steps,
                    "perturbation": perturbation,
                },
            )
            await reactor.send_command("start", {})

            @reactor.on_event
            def _capture(event: dict[str, Any]) -> None:
                events.append(event)

            await asyncio.sleep(2.0)

        cf_steps = steps[: perturbation.get("step", 0) + 1]
        cf_steps.append(
            {
                "t": perturbation.get("step", 0),
                "reactor_perturbed": True,
                "perturbation": perturbation,
                "events": events[:20],
            }
        )
        return {
            "nominal": steps,
            "counterfactual": cf_steps,
            "perturbation": perturbation,
            "provider": "reactor",
            "model": self.model_name,
            "events": events[:50],
        }
