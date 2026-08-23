from __future__ import annotations

from typing import Any, Protocol

from schemas.task import TaskConfig


class PolicyAdapter(Protocol):
    observation_space: dict[str, Any]
    action_space: dict[str, Any]

    def reset(self, task: TaskConfig) -> dict[str, Any]: ...

    def act(self, observation: dict[str, Any], instruction: str) -> dict[str, Any]: ...

    def metadata(self) -> dict[str, Any]: ...


class WorldModelProvider(Protocol):
    def rollout(self, scenario: dict[str, Any], policy: PolicyAdapter) -> dict[str, Any]: ...

    def counterfactual(
        self, trajectory: dict[str, Any], perturbation: dict[str, Any]
    ) -> dict[str, Any]: ...


class RecoveryPolicy(Protocol):
    def propose(
        self,
        observation: dict[str, Any],
        failure: dict[str, Any],
        goal: dict[str, Any],
        history: list[dict[str, Any]],
    ) -> list[str]: ...
