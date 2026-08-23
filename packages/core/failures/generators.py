from __future__ import annotations

import math
import random
from abc import ABC, abstractmethod
from typing import Any

from schemas.failure import FailureEvent, FailureSpec, FailureType
from schemas.task import TaskConfig


class FailureGenerator(ABC):
    failure_type: FailureType

    @abstractmethod
    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        ...

    @abstractmethod
    def apply(self, env: Any, event: FailureEvent) -> None:
        ...


class ObjectSlipGenerator(FailureGenerator):
    failure_type = FailureType.OBJECT_SLIP

    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        spec: FailureSpec | None = base_context.get("spec")
        max_steps = base_context.get("max_steps", 200)
        if spec and spec.deterministic and spec.time is not None:
            t = spec.time
            severity = spec.severity or 0.5
            direction = spec.parameters.get("direction", "negative_y")
        else:
            t_start, t_end = 20, max(30, max_steps // 2)
            t = rng.uniform(t_start, t_end) if spec is None or not spec.deterministic else (spec.time or 30.0)
            severity = rng.uniform(0.2, 0.8) if spec is None or spec.severity is None else spec.severity
            direction = rng.choice(["negative_y", "positive_y", "negative_x", "positive_x"])
        seed = base_context.get("seed", 0)
        return FailureEvent(
            type=self.failure_type,
            seed=seed,
            time=float(t),
            severity=float(severity),
            step=int(t),
            direction=direction,
            sampled_params={"direction": direction, "slip_distance": severity * 0.15},
        )

    def apply(self, env: Any, event: FailureEvent) -> None:
        env.force_slip(event.severity, event.direction or "negative_y")


class GraspMissGenerator(FailureGenerator):
    failure_type = FailureType.GRASP_MISS

    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        spec = base_context.get("spec")
        max_steps = base_context.get("max_steps", 200)
        t = spec.time if spec and spec.time is not None else rng.uniform(15, max_steps // 3)
        severity = spec.severity if spec and spec.severity is not None else rng.uniform(0.3, 0.7)
        return FailureEvent(
            type=self.failure_type,
            seed=base_context.get("seed", 0),
            time=float(t),
            severity=float(severity),
            step=int(t),
            sampled_params={"miss_offset": severity * 0.1},
        )

    def apply(self, env: Any, event: FailureEvent) -> None:
        env.force_grasp_miss()


class TargetShiftGenerator(FailureGenerator):
    failure_type = FailureType.TARGET_SHIFT

    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        spec = base_context.get("spec")
        t = spec.time if spec and spec.time is not None else rng.uniform(40, 80)
        severity = spec.severity if spec and spec.severity is not None else rng.uniform(0.3, 0.9)
        return FailureEvent(
            type=self.failure_type,
            seed=base_context.get("seed", 0),
            time=float(t),
            severity=float(severity),
            step=int(t),
            sampled_params={"shift_x": severity * 0.12, "shift_y": severity * 0.08},
        )

    def apply(self, env: Any, event: FailureEvent) -> None:
        env.shift_target(event.severity)


class ActuatorDeviationGenerator(FailureGenerator):
    failure_type = FailureType.ACTUATOR_DEVIATION

    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        spec = base_context.get("spec")
        severity = spec.severity if spec and spec.severity is not None else rng.uniform(0.1, 0.5)
        return FailureEvent(
            type=self.failure_type,
            seed=base_context.get("seed", 0),
            time=float(spec.time if spec and spec.time else 10),
            severity=float(severity),
            step=int(spec.time if spec and spec.time else 10),
            sampled_params={"bias_x": severity * 0.03, "bias_y": -severity * 0.02},
        )

    def apply(self, env: Any, event: FailureEvent) -> None:
        env.actuator_bias = (event.sampled_params["bias_x"], event.sampled_params["bias_y"])


class SensorNoiseGenerator(FailureGenerator):
    failure_type = FailureType.SENSOR_NOISE

    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        spec = base_context.get("spec")
        severity = spec.severity if spec and spec.severity is not None else rng.uniform(0.05, 0.3)
        return FailureEvent(
            type=self.failure_type,
            seed=base_context.get("seed", 0),
            time=float(spec.time if spec and spec.time else 5),
            severity=float(severity),
            step=int(spec.time if spec and spec.time else 5),
            sampled_params={"noise_std": severity * 0.05},
        )

    def apply(self, env: Any, event: FailureEvent) -> None:
        std = event.sampled_params["noise_std"]
        env.sensor_noise = (std, std)


class OcclusionGenerator(FailureGenerator):
    failure_type = FailureType.OCCLUSION

    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        spec = base_context.get("spec")
        severity = spec.severity if spec and spec.severity is not None else rng.uniform(0.5, 1.0)
        return FailureEvent(
            type=self.failure_type,
            seed=base_context.get("seed", 0),
            time=float(spec.time if spec and spec.time else 25),
            severity=float(severity),
            step=int(spec.time if spec and spec.time else 25),
            sampled_params={"duration_steps": int(severity * 20)},
        )

    def apply(self, env: Any, event: FailureEvent) -> None:
        env.occlusion = True


class ObstacleAppearsGenerator(FailureGenerator):
    failure_type = FailureType.OBSTACLE_APPEARS

    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        spec = base_context.get("spec")
        severity = spec.severity if spec and spec.severity is not None else rng.uniform(0.4, 0.9)
        return FailureEvent(
            type=self.failure_type,
            seed=base_context.get("seed", 0),
            time=float(spec.time if spec and spec.time else 35),
            severity=float(severity),
            step=int(spec.time if spec and spec.time else 35),
            sampled_params={"obstacle_x": 0.5, "obstacle_y": 0.4},
        )

    def apply(self, env: Any, event: FailureEvent) -> None:
        env.obstacle = (event.sampled_params["obstacle_x"], event.sampled_params["obstacle_y"])


class CompositeGenerator(FailureGenerator):
    failure_type = FailureType.COMPOSITE_FAILURE

    def __init__(self, components: list[FailureGenerator] | None = None):
        self.components = components or [
            ObjectSlipGenerator(),
            OcclusionGenerator(),
        ]

    def sample(self, base_context: dict[str, Any], rng: random.Random) -> FailureEvent:
        n = rng.randint(2, min(3, len(self.components)))
        chosen = rng.sample(self.components, n)
        sub_events = [g.sample(base_context, rng) for g in chosen]
        return FailureEvent(
            type=self.failure_type,
            seed=base_context.get("seed", 0),
            time=min(e.time for e in sub_events),
            severity=max(e.severity for e in sub_events),
            step=min(e.step for e in sub_events),
            components=sub_events,
            sampled_params={"component_types": [e.type.value for e in sub_events]},
        )

    def apply(self, env: Any, event: FailureEvent) -> None:
        for comp in event.components:
            gen = GENERATOR_REGISTRY.get(comp.type)
            if gen:
                gen.apply(env, comp)


GENERATOR_REGISTRY: dict[FailureType, FailureGenerator] = {
    FailureType.OBJECT_SLIP: ObjectSlipGenerator(),
    FailureType.GRASP_MISS: GraspMissGenerator(),
    FailureType.TARGET_SHIFT: TargetShiftGenerator(),
    FailureType.ACTUATOR_DEVIATION: ActuatorDeviationGenerator(),
    FailureType.SENSOR_NOISE: SensorNoiseGenerator(),
    FailureType.OCCLUSION: OcclusionGenerator(),
    FailureType.OBSTACLE_APPEARS: ObstacleAppearsGenerator(),
    FailureType.COMPOSITE_FAILURE: CompositeGenerator(),
}


def sample_failure(
    failure_type: FailureType,
    seed: int,
    task: TaskConfig,
    spec: FailureSpec | None = None,
) -> FailureEvent:
    rng = random.Random(seed)
    gen = GENERATOR_REGISTRY[failure_type]
    ctx = {"seed": seed, "max_steps": task.max_steps, "spec": spec}
    return gen.sample(ctx, rng)


def apply_failure(env: Any, event: FailureEvent) -> None:
    if event.type == FailureType.COMPOSITE_FAILURE:
        GENERATOR_REGISTRY[FailureType.COMPOSITE_FAILURE].apply(env, event)
    else:
        GENERATOR_REGISTRY[event.type].apply(env, event)


def is_within_tolerance(observed: dict[str, Any], expected: dict[str, Any], tol: float) -> bool:
    dx = abs(observed.get("object_x", 0) - expected.get("object_x", 0))
    dy = abs(observed.get("object_y", 0) - expected.get("object_y", 0))
    return math.hypot(dx, dy) <= tol
