from __future__ import annotations

from typing import Any, Callable

from core.evaluation.scoring import aggregate_metrics
from core.evaluation.splits import assign_scenario_split, sample_failure_spec
from core.recovery.rule_recovery import RecoveryPolicy, RuleRecoveryPolicy
from core.scenario.engine import ScenarioEngine
from policies.nominal import NominalPolicy
from policies.smolvla import SmolVLARecovery, SmolVLAProvider
from schemas.benchmark import PROFILE_EPISODES, BenchmarkProfile
from schemas.task import TaskConfig

PolicyFactory = Callable[[], Any]
RecoveryFactory = Callable[[], RecoveryPolicy] | None


class Method:
    """A row in the comparison matrix: which policy acts, and who recovers."""

    def __init__(self, name: str, policy: PolicyFactory, recovery: RecoveryFactory = None):
        self.name = name
        self.policy = policy
        self.recovery = recovery


METHODS: dict[str, Method] = {
    "baseline": Method("baseline", NominalPolicy),
    "rule": Method("rule", NominalPolicy, RuleRecoveryPolicy),
    "smolvla_zeroshot": Method("smolvla_zeroshot", lambda: SmolVLAProvider(fine_tuned=False)),
    "smolvla_finetuned": Method(
        "smolvla_finetuned",
        lambda: SmolVLAProvider(fine_tuned=True, checkpoint="smolvla-recovery-v1"),
        SmolVLARecovery,
    ),
}

POLICY_FACTORIES: dict[str, PolicyFactory] = {
    "nominal": NominalPolicy,
    "smolvla": lambda: SmolVLAProvider(fine_tuned=False),
    "smolvla_ft": lambda: SmolVLAProvider(fine_tuned=True, checkpoint="smolvla-recovery-v1"),
}


def _episode(
    engine: ScenarioEngine,
    method: Method,
    seed: int,
    split: str,
) -> dict[str, Any]:
    spec = sample_failure_spec(split, seed)
    recovery_policy = method.recovery() if method.recovery else None
    artifact = engine.run_episode(
        policy=method.policy(),
        task=TaskConfig(),
        seed=seed,
        failure_spec=spec,
        recovery=recovery_policy is not None,
        recovery_policy=recovery_policy,
    )
    artifact.is_ood = split == "ood"
    payload = artifact.model_dump()
    payload["split"] = split
    payload["method"] = method.name
    return payload


def _episode_metrics(episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for episode in episodes:
        row = dict(episode.get("metrics", {}))
        row["is_ood"] = episode.get("is_ood", False)
        row["recovery_score"] = episode.get("recovery_score", 0.0)
        rows.append(row)
    return rows


def run_evaluation(
    profile: BenchmarkProfile = BenchmarkProfile.QUICK,
    episodes: int | None = None,
    policy_id: str = "nominal",
    recovery: bool = True,
    compare_baseline: bool = True,
    seed_base: int = 0,
) -> dict[str, Any]:
    """Run one benchmark suite. Honours the requested policy and split protocol."""
    total = episodes or PROFILE_EPISODES[profile]
    engine = ScenarioEngine()
    policy_factory = POLICY_FACTORIES.get(policy_id, NominalPolicy)

    under_test = Method(policy_id, policy_factory, RuleRecoveryPolicy if recovery else None)
    baseline = Method("baseline", policy_factory)

    force_ood = profile is BenchmarkProfile.OOD
    results: list[dict[str, Any]] = []
    baseline_results: list[dict[str, Any]] = []

    for index in range(total):
        seed = seed_base + index
        spec = sample_failure_spec("ood" if force_ood else "train", seed)
        split = (
            "ood"
            if force_ood
            else assign_scenario_split(index, spec.type, spec.severity or 0.0, seed)
        )
        results.append(_episode(engine, under_test, seed, split))
        if compare_baseline:
            baseline_results.append(_episode(engine, baseline, seed, split))

    return {
        "episodes": results,
        "baseline_episodes": baseline_results,
        "metrics": aggregate_metrics(_episode_metrics(results)),
        "baseline_metrics": aggregate_metrics(_episode_metrics(baseline_results)),
    }


def run_comparison(
    known_episodes: int = 12,
    ood_episodes: int = 8,
    seed_base: int = 100,
) -> dict[str, Any]:
    """Measure every method on known and held-out OOD scenarios. Measured rates only."""
    engine = ScenarioEngine()
    known: dict[str, Any] = {}
    ood: dict[str, Any] = {}

    for name, method in METHODS.items():
        known_eps = [_episode(engine, method, seed_base + i, "train") for i in range(known_episodes)]
        ood_eps = [
            _episode(engine, method, seed_base + 10_000 + i, "ood") for i in range(ood_episodes)
        ]
        known[name] = _report(aggregate_metrics(_episode_metrics(known_eps)), known_episodes)
        ood[name] = _report(aggregate_metrics(_episode_metrics(ood_eps)), ood_episodes)

    return {
        "known": known,
        "ood": ood,
        "protocol": "OOD = severity 0.65-0.85 and composite failures, never used for training",
        "summary_table": [
            {
                "method": name,
                "known_success_pct": round(known[name]["final_success_rate"] * 100, 1),
                "ood_success_pct": round(ood[name]["final_success_rate"] * 100, 1),
            }
            for name in METHODS
        ],
    }


def _report(metrics: dict[str, float], n: int) -> dict[str, Any]:
    return {
        "final_success_rate": metrics.get("final_success_rate", 0.0),
        "recovery_success_rate": metrics.get("recovery_success_rate", 0.0),
        "detection_rate": metrics.get("failure_detection_rate", 0.0),
        "robustness_score": metrics.get("robustness_score", 0.0),
        "n": n,
    }
