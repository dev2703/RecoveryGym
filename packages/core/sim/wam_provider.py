from __future__ import annotations

import hashlib
import json
from typing import Any

from core.storage.artifacts import ArtifactStore
from policies.base import WorldModelProvider


class MockWAMProvider:
    """Mock world model for local dev."""

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

    def __init__(self, api_key: str | None = None, use_mock: bool = True):
        self.api_key = api_key
        self.use_mock = use_mock
        self._mock = MockWAMProvider()
        self._cache: dict[str, dict[str, Any]] = {}
        self.call_count = 0

    def rollout(self, scenario: dict[str, Any], policy: Any) -> dict[str, Any]:
        if self.use_mock or not self.api_key:
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
        )
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.use_mock or not self.api_key:
            result = self._mock.counterfactual(trajectory, perturbation)
        else:
            self.call_count += 1
            result = self._mock.counterfactual(trajectory, perturbation)

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
