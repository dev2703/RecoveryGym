from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from core.config import Settings, get_settings
from core.sim.reactor_client import ReactorClient, ReactorError
from core.storage.artifacts import ArtifactStore
from policies.base import WorldModelProvider

logger = logging.getLogger(__name__)


class MockWAMProvider:
    """Local counterfactual for development and tests only."""

    version = "mock-wam-1.0"

    def rollout(self, scenario: dict[str, Any], policy: Any) -> dict[str, Any]:
        return {"trajectory": scenario.get("trajectory", []), "provider": "mock"}

    def counterfactual(
        self, trajectory: dict[str, Any], perturbation: dict[str, Any]
    ) -> dict[str, Any]:
        steps = trajectory.get("steps", [])
        t = perturbation.get("step", 0)
        cf_steps = steps[: t + 1] + [{"t": t, "perturbed": True, **perturbation}] + steps[t + 1 :]
        return {
            "nominal": steps,
            "counterfactual": cf_steps,
            "perturbation": perturbation,
            "provider": "mock",
        }


class WAMProvider(WorldModelProvider):
    """Reactor/WAM provider with local cache."""

    version = "wam-1.0"

    def __init__(
        self,
        api_key: str | None = None,
        use_mock: bool | None = None,
        model_name: str | None = None,
        counterfactual_command: str | None = None,
        settings: Settings | None = None,
    ):
        cfg = settings or get_settings()
        self.api_key = api_key if api_key is not None else cfg.reactor_api_key
        self.use_mock = cfg.use_mock_wam if use_mock is None else use_mock
        self.model_name = model_name or cfg.reactor_model_name
        self.counterfactual_command = (
            counterfactual_command or cfg.reactor_counterfactual_command
        )
        self._mock = MockWAMProvider()
        self._cache: dict[str, dict[str, Any]] = {}
        self.call_count = 0
        self._client: ReactorClient | None = None

    def _reactor(self) -> ReactorClient:
        if not self.api_key:
            raise ReactorError("REACTOR_API_KEY is required when USE_MOCK_WAM=false")
        if self._client is None:
            self._client = ReactorClient(
                api_key=self.api_key,
                model_name=self.model_name,
                counterfactual_command=self.counterfactual_command,
            )
        return self._client

    def rollout(self, scenario: dict[str, Any], policy: Any) -> dict[str, Any]:
        if self.use_mock:
            return self._mock.rollout(scenario, policy)
        self.call_count += 1
        return self._mock.rollout(scenario, policy)

    def counterfactual(
        self, trajectory: dict[str, Any], perturbation: dict[str, Any]
    ) -> dict[str, Any]:
        cache_key = ArtifactStore.cache_key(
            trajectory.get("seed"),
            perturbation,
            self.version,
            self.model_name,
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.use_mock:
            result = self._mock.counterfactual(trajectory, perturbation)
        else:
            self.call_count += 1
            try:
                result = self._reactor().counterfactual(trajectory, perturbation)
            except Exception as error:
                logger.exception("Reactor counterfactual failed")
                raise ReactorError(str(error)) from error

        self._cache[cache_key] = result
        return result

    def run_counterfactual_episode(
        self, nominal_trajectory: dict[str, Any], failure_event: dict[str, Any]
    ) -> dict[str, Any]:
        perturbation = {
            "step": failure_event.get("step", 0),
            "type": failure_event.get("type"),
            "severity": failure_event.get("severity"),
        }
        return self.counterfactual(nominal_trajectory, perturbation)
