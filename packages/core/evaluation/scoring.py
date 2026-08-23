from __future__ import annotations


def compute_recovery_score(metrics: dict[str, float]) -> float:
    return (
        0.40 * metrics.get("task_recovered", 0.0)
        + 0.20 * metrics.get("detection_score", 0.0)
        + 0.15 * metrics.get("safety_score", 1.0)
        + 0.15 * metrics.get("efficiency_score", 0.0)
        + 0.10 * metrics.get("latency_score", 0.0)
    )


def aggregate_metrics(episodes: list[dict]) -> dict[str, float]:
    if not episodes:
        return {}
    n = len(episodes)
    return {
        "nominal_success_rate": sum(e.get("nominal_success", 0) for e in episodes) / n,
        "failure_detection_rate": sum(e.get("detection_score", 0) for e in episodes) / n,
        "diagnosis_accuracy": sum(e.get("diagnosis_correct", 0) for e in episodes) / n,
        "recovery_success_rate": sum(e.get("task_recovered", 0) for e in episodes) / n,
        "final_success_rate": sum(e.get("final_success", 0) for e in episodes) / n,
        "median_recovery_latency": sorted(e.get("recovery_latency", 0) for e in episodes)[n // 2],
        "safety_violation_rate": sum(e.get("safety_violations", 0) for e in episodes) / n,
        "avg_corrective_actions": sum(e.get("corrective_actions", 0) for e in episodes) / n,
        "ood_recovery_success": sum(e.get("task_recovered", 0) for e in episodes if e.get("is_ood")) / max(
            1, sum(1 for e in episodes if e.get("is_ood"))
        ),
        "robustness_score": sum(e.get("recovery_score", 0) for e in episodes) / n * 100,
    }
