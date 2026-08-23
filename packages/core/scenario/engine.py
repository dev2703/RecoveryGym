from __future__ import annotations

import uuid
from typing import Any

from core.detection.detector import FailureDetector
from core.evaluation.scoring import compute_recovery_score
from core.failures.generators import apply_failure, sample_failure
from core.recovery.rule_recovery import RecoveryPolicy, RuleRecoveryPolicy, get_recovery_plan
from core.recovery.safety import SafetyGate
from core.simulator.pick_place import PickPlaceEnv
from policies.base import PolicyAdapter
from policies.nominal import NominalPolicy
from schemas.episode import EpisodeArtifact, EpisodeOutcome
from schemas.failure import FailureEvent, FailureSpec, FailureType
from schemas.task import TaskConfig
from schemas.trajectory import EpisodeEvent, Trajectory, TrajectoryStep

# Slip and grasp-miss only mean something while the object is held, so they wait
# for that precondition instead of firing at a wall-clock step.
GRASP_DEPENDENT = (FailureType.OBJECT_SLIP, FailureType.GRASP_MISS)

DEFAULT_FAILURE = FailureSpec(
    type=FailureType.OBJECT_SLIP,
    seed=0,
    time=30.0,
    severity=0.5,
    deterministic=True,
)


class ScenarioEngine:
    """Runs one episode: nominal rollout, perturbation, detection, recovery, scoring."""

    def run_episode(
        self,
        policy: PolicyAdapter | None = None,
        task: TaskConfig | None = None,
        seed: int = 42,
        failure_spec: FailureSpec | None = None,
        recovery: bool = True,
        recovery_policy: RecoveryPolicy | None = None,
    ) -> EpisodeArtifact:
        policy = policy or NominalPolicy()
        task = task or TaskConfig()
        env = PickPlaceEnv(task, seed=seed)
        detector = FailureDetector(task)
        safety = SafetyGate(task)
        recoverer = recovery_policy or RuleRecoveryPolicy()

        policy.reset(task)
        detector.reset()
        safety.reset()

        failure_event = self._resolve_failure(failure_spec, seed, task)
        nominal_trajectory = Trajectory()
        full_trajectory = Trajectory()
        recovery_steps: list[TrajectoryStep] = []
        events: list[EpisodeEvent] = []

        injected = False
        detected_type: FailureType | None = None
        recovering = False
        recovery_start_t = 0
        corrective_actions = 0

        for t in range(task.max_steps):
            observation = env.get_observation()

            if recovering:
                action = recoverer.act(observation)
                corrective_actions += 1
            else:
                action = policy.act(observation, task.instruction)
                detector.observe(observation, action)

            safe_action = safety.validate_action(env.state, action)
            step = TrajectoryStep(
                t=t, state=env.snapshot(), action=safe_action, observation=observation
            )
            full_trajectory.append(step)
            if recovering:
                recovery_steps.append(step)
            else:
                nominal_trajectory.append(step)

            observation, done = env.step(safe_action)

            if failure_event and not injected and self._ready_to_inject(failure_event, env, t, done):
                apply_failure(env, failure_event)
                injected = True
                done = False
                events.append(
                    EpisodeEvent(
                        t=t, event="FAILURE_INJECTED", failure_type=failure_event.type.value
                    )
                )
                observation = env.get_observation()

            if injected and detected_type is None:
                detected_type, confidence, _ = detector.detect(observation)
                if detected_type is not None:
                    events.append(
                        EpisodeEvent(
                            t=t,
                            event="FAILURE_DETECTED",
                            failure_type=detected_type.value,
                            confidence=confidence,
                        )
                    )
                    if recovery:
                        recovering = True
                        recovery_start_t = t
                        plan = recoverer.start(detected_type)
                        events.append(
                            EpisodeEvent(
                                t=t,
                                event="RECOVERY_STARTED",
                                policy=recoverer.name,
                                details={"plan": plan},
                            )
                        )
                    done = False

            if recovering and recoverer.is_done() and env.is_success():
                done = True

            if done:
                break

        success = env.is_success()
        recovered = injected and success

        if recovering:
            events.append(EpisodeEvent(t=env.t, event="RECOVERY_VERIFIED", success=recovered))

        metrics = self._score(
            failure_event=failure_event,
            detected_type=detected_type,
            success=success,
            recovered=recovered,
            latency=max(0, env.t - recovery_start_t) if recovering else 0,
            safety_violations=safety.violations,
            corrective_actions=corrective_actions,
        )

        return EpisodeArtifact(
            episode_id=f"ep_{uuid.uuid4().hex[:8]}",
            task_id=task.task_id.value,
            seed=seed,
            initial_state=env.snapshot(),
            nominal_trajectory=nominal_trajectory,
            perturbed_trajectory=full_trajectory,
            failure_event=failure_event,
            failure_observation=env.get_observation(),
            expert_recovery={
                "primitives": get_recovery_plan(failure_event.type) if failure_event else [],
                "policy": recoverer.name if recovering else None,
                "start_t": recovery_start_t if recovering else None,
                "trajectory": [s.model_dump() for s in recovery_steps],
            },
            events=events,
            outcome=EpisodeOutcome.SUCCESS if success else EpisodeOutcome.FAILURE,
            recovery_score=compute_recovery_score(metrics),
            metrics=metrics,
        )

    def _resolve_failure(
        self, spec: FailureSpec | None, seed: int, task: TaskConfig
    ) -> FailureEvent | None:
        if spec is None:
            spec = DEFAULT_FAILURE.model_copy(update={"seed": seed})
        if spec.type is None:
            return None
        return sample_failure(spec.type, seed, task, spec)

    def _ready_to_inject(
        self, event: FailureEvent, env: PickPlaceEnv, t: int, task_finished: bool
    ) -> bool:
        if event.type in GRASP_DEPENDENT:
            return bool(env.state["grasped"])
        # Otherwise honour the scheduled step, but never let the episode end
        # without the perturbation it was configured to carry.
        return t >= event.step or task_finished

    def _score(
        self,
        failure_event: FailureEvent | None,
        detected_type: FailureType | None,
        success: bool,
        recovered: bool,
        latency: int,
        safety_violations: int,
        corrective_actions: int,
    ) -> dict[str, float]:
        detected = detected_type is not None
        if failure_event is None:
            diagnosis = 0.0
        elif failure_event.type == FailureType.COMPOSITE_FAILURE:
            diagnosis = 0.5 if detected else 0.0
        else:
            diagnosis = 1.0 if detected_type == failure_event.type else 0.0

        return {
            "nominal_success": 1.0 if success and failure_event is None else 0.0,
            "detection_score": 1.0 if detected else 0.0,
            "diagnosis_correct": diagnosis,
            "task_recovered": 1.0 if recovered else 0.0,
            "final_success": 1.0 if success else 0.0,
            "recovery_latency": float(latency),
            "safety_violations": float(safety_violations),
            "corrective_actions": float(corrective_actions),
            "safety_score": max(0.0, 1.0 - safety_violations * 0.2),
            "efficiency_score": max(0.0, 1.0 - corrective_actions / 50.0),
            "latency_score": max(0.0, 1.0 - latency / 100.0),
        }
