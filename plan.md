# RecoveryGym — Hackathon Build Plan

> **Make your robot sweat.**
>
> Learn **when** a policy fails, **what kind** of failure it was, and **whether** a recovery policy can bring the task back — then generate corrective experience, fine-tune, and re-test.
>
> RecoveryGym is a complete robot gym for robustness and recovery: upload a policy, break it thousands of ways, measure failure, recover, adapt, and compare.

---

## One-sentence product

**RecoveryGym** stress-tests robot policies against deterministic, stochastic, distribution-shifted, and compositional failures; evaluates detection and recovery; generates corrective trajectories; and optionally fine-tunes a small pretrained foundation policy to improve recovery.

### Core customer loop

```
Upload Policy
      ↓
Upload Task / Environment
      ↓
RecoveryGym generates thousands of counterfactual + stochastic rollouts
      ↓
Failure taxonomy + robustness report
      ↓
Recovery evaluation
      ↓
Corrective trajectories / dataset
      ↓
Fine-tune recovery policy
      ↓
Re-run benchmark
      ↓
Compare before vs after
```

---

## 0. Important scope decision

Do **not** position the hackathon submission as “we invented robot failure recovery.” That space already contains recent failure-aware VLA work and recovery-aware benchmarks (e.g. FLARE, SO-101-style failure/recovery benchmarks, agentic recovery under disturbances). There is also established infrastructure around OpenVLA and compact VLAs such as SmolVLA.

**Differentiated product direction:** the end-to-end robustness platform —

1. Upload an arbitrary policy  
2. Generate controlled + stochastic + compositional failures at scale  
3. Evaluate detection and recovery  
4. Produce recovery data  
5. Fine-tune a recovery specialist  
6. Re-test on held-out / OOD failures  

Do **not** make novelty claims beyond the specific system/product integration actually implemented.

**Positioning:** RecoveryGym is not “a robot that can recover.” It is **a robustness and recovery evaluation platform for robot policies** — a complete robot gym.

---

## 1. Product thesis

### The problem

Robot policies can look strong on nominal success rates while failing unpredictably under perturbations, execution noise, distribution shifts, and novel combinations of failures.

### Four questions RecoveryGym must answer

1. **When** does the policy fail?  
2. **What kind** of failure occurred?  
3. **Can** a recovery policy recover the task?  
4. **Can** generated recovery experience improve a recovery policy?

### Robustness ladder (keep these separated)

```
Nominal robustness
        ↓
Known failure robustness
        ↓
Stochastic robustness
        ↓
Distribution-shift robustness
        ↓
Compositional / novel-failure robustness
```

A policy that succeeds on failures it saw during training is **not** evidence of general recovery.

---

## 2. Core architecture

Keep the architecture intentionally small.

```
                           VERCEL FRONTEND
                                │
                                │ HTTPS
                                ▼
                         MODAL API / JOBS
                                │
                 ┌──────────────┼──────────────┐
                 │              │              │
                 ▼              ▼              ▼
          Scenario Engine   Policy Runner   Evaluator
                 │              │              │
                 ▼              │              │
             Reactor/WAM       │              │
         simulation / rollout  │              │
                                │              │
                ┌───────────────┘              │
                ▼                              │
          Recovery Engine                      │
          ├─ Rule Policy                       │
          ├─ Learned Policy                    │
          ├─ Foundation VLA                    │
          └─ WAM / model adapter               │
                                │              │
                                └──────┬───────┘
                                       ▼
                              REPORT + DATASET
                                       │
                                       ▼
                                Optional training
                                       │
                                       ▼
                                Improved recovery
                                       │
                                       ▼
                                  Re-benchmark
```

### Architectural principle

**RecoveryGym owns the benchmark protocol. Models are plug-ins.**

The benchmark must not be tied to WAM, SmolVLA, OpenVLA, GR00T, or one simulator.

### Core interfaces

```python
class PolicyAdapter:
    def reset(self, task): ...
    def act(self, observation, instruction): ...
    def metadata(self): ...

class WorldModelProvider:
    def rollout(self, scenario, policy): ...
    def counterfactual(self, trajectory, perturbation): ...

class RecoveryPolicy:
    def propose(self, observation, failure, goal, history): ...
```

Implement local/mock providers first. Plug Reactor/WAM into the same interface.

---

## 3. Scope of the hackathon MVP

### Task

One manipulation task first:

> Pick up object → move it → place it in target.

Optional second task only after the first is reliable:

> Pick object → avoid obstacle → place object.

Configurable axes:

- object position  
- target position  
- object identity / visual appearance (if supported)  
- obstacle position  
- camera / observation noise  
- actuator noise  
- timing  
- failure severity  

### Failure types (start with 6–8)

| ID | Name |
|----|------|
| `GRASP_MISS` | Grasp miss |
| `OBJECT_SLIP` | Object slip |
| `TARGET_SHIFT` | Target shift |
| `ACTUATOR_DEVIATION` | Actuator deviation |
| `SENSOR_NOISE` | Sensor noise |
| `OCCLUSION` | Occlusion |
| `OBSTACLE_APPEARS` | Obstacle appears |
| `COMPOSITE_FAILURE` | Composite failure |

Do **not** add 30 failure classes in the hackathon. Keep a flexible schema so more can be added later.

---

## 4. Failure engine: deterministic + stochastic + novel

This is a core differentiator — design it properly from day one.

### 4.1 Deterministic failures

Fixed seeds + explicit parameters for regression testing.

```json
{
  "type": "OBJECT_SLIP",
  "seed": 42,
  "time": 3.2,
  "severity": 0.5,
  "direction": "negative_y"
}
```

Same scenario must reproduce exactly.

**Purpose:** unit tests, debugging, baseline comparisons, regression suite, reproducible leaderboard-style evaluation.

### 4.2 Stochastic failures

Sample failure parameters from distributions — do not hard-code one “noise = failure” value.

Examples:

- `slip_time` ~ Uniform(t_start, t_end)  
- `slip_distance` ~ LogNormal(μ, σ)  
- `slip_direction` ~ Uniform(0, 2π)  
- `actuator_bias` ~ Normal(0, Σ)  
- `sensor_noise` ~ Normal(0, Σ_sensor)  
- `latency` ~ LogNormal(...)  
- `object_friction` ~ distribution conditioned on object  

Every rollout records seed + sampled parameters:

```json
{
  "type": "OBJECT_SLIP",
  "seed": 18372,
  "sampled_params": {}
}
```

Supports exact reproduction **and** distribution-level robustness testing.

### 4.3 Separate normal variation from failure

Not every deviation is a failure.

```
Expected variation  →  normal state
Large / persistent / task-breaking deviation  →  failure candidate
```

Do **not** train the detector on “noise = failure.”

Store an `expected_uncertainty` / tolerance model per task. Hackathon MVP: calibrated thresholds + empirical state distributions. Later: learned probabilistic dynamics.

### 4.4 Distribution shift

Failures that are not simply time-series noise:

- new object mass / dimensions  
- unseen target positions  
- changed friction  
- camera viewpoint shift  
- lighting change  
- sensor dropout  
- control-frequency variation  

Mark as `DISTRIBUTION_SHIFT` / `OOD_SCENARIO` even when no instantaneous failure event exists.

### 4.5 Compositional failures

Combine perturbations, e.g.:

- `OBJECT_SLIP` + `OCCLUSION`  
- `ACTUATOR_DEVIATION` + `TARGET_SHIFT`  
- `SENSOR_NOISE` + `OBJECT_SLIP`  

Sample combinations randomly — critical for generalization evaluation.

---

## 5. Counterfactual rollout engine

Generate **paired** trajectories from the same initial state:

```
Same initial state
       │
       ├──────────────→ Nominal rollout
       │
       └──────────────→ Perturbed rollout
```

Given nominal trajectory `s0, a0, ..., sT`, choose intervention time `t`:

```
s'_t = Perturb(s_t, failure_event)
```

Then continue the rollout. Store:

- nominal trajectory  
- perturbed trajectory  
- failure metadata  
- counterfactual outcome  

Causal-ish at the scenario level: same start, controlled intervention, different outcome.

### WAM / Reactor usage

Use as the expensive world-model provider for:

- counterfactual future generation  
- high-fidelity / multimodal observations  
- difficult or ambiguous scenarios  

Do **not** call WAM for every control step if a cheaper local simulator can handle nominal rollouts.

```
cheap/local simulation
       ↓
identify candidate intervention points
       ↓
WAM/Reactor counterfactual rollout
       ↓
store resulting trajectories
```

Preserves Reactor credit budget and keeps the system faster.

---

## 6. Failure detection and diagnosis

Hybrid detector. Inputs:

- expected / predicted state  
- observed state  
- recent actions & observations  
- mission goal  

Residual: `r_t = distance(expected_state, observed_state)`

Layered approach (not a single hard threshold):

1. **Task invariants**  
2. **Residual / anomaly score**  
3. **Temporal persistence**  
4. **Semantic failure classifier** (optional; later VLM/VLA/WAM)

Example:

```
expected grasp = true
observed grasp = false
AND object position diverges
AND persistence > N frames
→ OBJECT_SLIP
```

---

## 7. Corrective policies — main research / product focus

Hierarchical recovery — not one monolithic policy:

```
Failure detector
      ↓
Recovery planner / policy selector
      ↓
Recovery primitive
      ↓
Low-level execution
      ↓
Verification
```

### Recovery primitives (reusable vocabulary)

`STOP` · `SAFE_STOP` · `RELOCALIZE` · `MOVE_TO_OBJECT` · `REGRASP` · `RELEASE` · `REALIGN` · `REROUTE` · `REPLAN` · `VERIFY_GRASP` · `VERIFY_TARGET` · `BACKTRACK` · `RESUME`

Different recovery methods share the same output interface.

---

## 8. Recovery policy tiers

### Tier A — deterministic rule baseline

Reliable and easy to debug. Example:

```
OBJECT_SLIP
→ STOP → MOVE_TO_OBJECT → REGRASP → VERIFY_GRASP → RESUME
```

Baseline only.

### Tier B — learned lightweight baseline

Small model answers: *which recovery primitive / short plan next?*

Possible model: MLP / small transformer over task embedding, state, recent trajectory, residual, detected failure, goal → recovery primitive / plan.

**Purpose:** learnable baseline, sample-efficiency measurement, low-compute specialist, comparison vs foundation-model route.

**Expected weakness:** limited OOD generalization; may memorize synthetic templates. Evaluation **must** include unseen seeds, severities, combinations, and scenario configs.

### Tier C — pretrained foundation VLA recovery policy

Preferred learnable path. **Recommended first model: SmolVLA (450M)** — compact VLA, LeRobot fine-tuning path, consumer-hardware friendly; single-A100 reference ~20k steps / ~4 hours. Use pretrained base, not train from scratch.

**Adapters also for:** OpenVLA, GR00T, other HF VLAs, Reactor/WAM if action interface exists.

OpenVLA (7B) and GR00T-class models are poor first fine-tune targets under hackathon budget — use for inference comparison or only if infra is already known-good.

---

## 9. How the foundation-model recovery policy should be trained

Teach **recovery behavior**, not the entire robot task from scratch.

```
INPUT
  Task: pick up red cube and place in blue tray.
  Recent observation history: ...
  Failure: object slipped from gripper.
  Goal state: cube in tray.

TARGET
  Recovery action chunk:
  STOP → MOVE_TO_OBJECT → REGRASP → VERIFY → RESUME
```

For a VLA consuming images + state + language, targets are short continuous action chunks from expert recovery trajectories. High-level primitive sequences stay as supervision/metadata.

### Data design

Do **not** create 10,000 nearly identical episodes. **Diversity > quantity.**

Stratify by: failure type, timing, severity, object position/appearance, robot state, camera viewpoint, noise, environment params, combinations.

Splits:

- 70% train / 15% val / 15% test  
- **Mandatory hard OOD test set** never used for training: new severity range, combinations, object params, timing ranges, perturbation distributions  

Without OOD, do not claim generalization.

---

## 10. “10k rollouts is not enough” — correct interpretation

Do not conclude fine-tuning is useless. A pretrained foundation policy already has a large representation prior; synthetic data teaches **recovery under perturbation**, not visual manipulation from scratch.

Synthetic data still overfits if failures are repetitive. Compare:

| ID | Method |
|----|--------|
| A | Zero-shot foundation model |
| B | Foundation + small recovery fine-tune |
| C | Rule-based recovery |
| D | Small learned recovery baseline |

Measure all four on: known failures, randomized known failures, OOD severity, OOD combinations, novel scenario configs.

**Important result:** Does recovery improve on **held-out and novel** perturbations? Not “99% on our generated data.”

---

## 11. Fine-tuning strategy under compute constraints

```
SmolVLA 450M
      ↓
parameter-efficient / targeted fine-tuning
      ↓
recovery dataset
      ↓
checkpoint
```

Use **Modal GPU** jobs (not the M3) for training. Start small; do not assume 20k steps is necessary — tune on validation/OOD.

If GPU budget tight:

- LoRA / PEFT if supported cleanly  
- Freeze most of visual backbone; adapt action/recovery components  
- Reduce observation frequency / action chunk count  
- Train on curated high-diversity subset  

**Do not** full-finetune 7B OpenVLA for this hackathon.

---

## 12. Recovery dataset format

Model-agnostic schema first:

```json
{
  "episode_id": "ep_001239",
  "task_id": "pick_place_v1",
  "seed": 18372,
  "embodiment": "wam",
  "initial_state": {},
  "nominal_trajectory": [],
  "failure_event": {
    "type": "OBJECT_SLIP",
    "time": 3.14,
    "severity": 0.63,
    "parameters": {}
  },
  "failure_observation": {},
  "expert_recovery": {
    "primitives": ["STOP", "MOVE_TO_OBJECT", "REGRASP", "VERIFY_GRASP", "RESUME"],
    "trajectory": []
  },
  "outcome": "SUCCESS",
  "recovery_score": 0.91
}
```

Export adapters into LeRobot/RLDS-like formats for VLA training. **Do not** make the core schema depend on LeRobot.

---

## 13. Recovery scoring

Do not collapse everything into success/failure.

**Components:** detection quality · diagnosis quality · task recovery success · recovery latency · action efficiency · path deviation · safety violations

Simple first score:

```
recovery_score =
    0.40 * task_recovered
  + 0.20 * detection_score
  + 0.15 * safety_score
  + 0.15 * efficiency_score
  + 0.10 * latency_score
```

Keep component scores visible.

### Report at least

- Nominal task success  
- Failure detection rate  
- Failure diagnosis accuracy  
- Recovery success rate  
- Final task success rate  
- Median recovery latency  
- Safety violation rate  
- Average corrective action count  
- OOD recovery success  

---

## 14. Main benchmark protocol

Every benchmark job runs at least:

1. Nominal  
2. Deterministic failures  
3. Stochastic failures  
4. Distribution-shift scenarios  
5. Compositional failures  
6. OOD failures  

Live demo: small episode counts. Backend batch: larger.

Example (configurable — **never hard-code**):

| Suite | Episodes |
|-------|----------|
| Nominal | 1,000 |
| Deterministic | 2,000 |
| Stochastic | 3,000 |
| Distribution shift | 2,000 |
| Compositional | 1,500 |
| OOD | 1,500 |
| **Total** | **~10,000** |

---

## 15. Evaluation methodology

### Required baselines

1. Customer/nominal policy without recovery  
2. Rule-based recovery  
3. Small learned recovery policy  
4. Zero-shot foundation model recovery  
5. Fine-tuned foundation model recovery  

Dashboard must make comparison visible. Example layout (numbers from **actual runs only**):

```
                        Final Success
Baseline                  xx%
Rule Recovery             xx%
MLP Recovery              xx%
Zero-shot SmolVLA         xx%
Fine-tuned SmolVLA        xx%
```

---

## 16. Anti-overfitting protocol (mandatory)

Synthetic simulation makes fake high scores easy. Rules:

1. **Split by scenario**, not frames — never mix frames from the same trajectory across train/test.  
2. **Hold out failure parameters** (e.g. train severity 0.1–0.6, test 0.6–0.8).  
3. **Hold out combinations** (train slip, occlusion; test slip + occlusion).  
4. **Hold out positions / environments.**  
5. **Report confidence intervals** (multi-seed mean ± std) where practical.  
6. **Track training/test distribution** — store generator config with every experiment.

---

## 17. Customer-facing workflow

Central frontend experience:

| Step | Action |
|------|--------|
| 1 | Upload policy (HF model ID or endpoint URL first; no arbitrary container day one) |
| 2 | Configure task / embodiment / obs / action / sim provider |
| 3 | Choose stress-test profile: Quick / Standard / Adversarial / OOD / Custom |
| 4 | Run benchmark (progress: episodes, failures generated, recoveries attempted) |
| 5 | Show report (robustness score + breakdown) |
| 6 | Generate recovery dataset (download) |
| 7 | Fine-tune (enqueue Modal training job) |
| 8 | Re-test (before vs after, including OOD) |

Only use real measured values in reports.

---

## 18. Frontend architecture

**Stack:** Next.js · Tailwind · shadcn/ui · Recharts (or light charts) · Canvas/SVG for sim viz · Vercel · v0 for shell only (not backend logic)

### Main views

| Route | Role |
|-------|------|
| `/` | Landing / product |
| `/playground` | Interactive single rollout (**priority**) |
| `/benchmark` | Long-running stress test |
| `/runs/:id` | Replay + timeline |
| `/reports/:id` | Customer report (**priority**) |
| `/train/:id` | Fine-tune status + before/after |

---

## 19. Backend architecture

FastAPI on Modal. Suggested boundaries:

```
api/          runs, benchmarks, policies, training
core/         scenarios, failures, detector, recovery, evaluator
sim/          local_env, reactor_provider
policies/     base, rule, learned, smolvla, wam adapters
training/     dataset, export_lerobot, finetune
storage/      artifacts, db
```

Dependency direction: **API → core → providers**. Never put provider-specific logic inside the evaluator.

---

## 20. API endpoints (keep small)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/v1/runs` | One interactive scenario |
| `POST` | `/v1/benchmarks` | Launch batch evaluation → job id |
| `GET` | `/v1/benchmarks/{id}` | Progress + results |
| `POST` | `/v1/policies` | Register policy endpoint / model ref |
| `POST` | `/v1/datasets/{benchmark_id}/generate` | Corrective dataset |
| `POST` | `/v1/training` | Launch fine-tune |
| `GET` | `/v1/training/{id}` | Training status |

No large RPC framework.

---

## 21. Asynchronous jobs

```
POST benchmark → job ID → Modal job → artifacts → frontend polls
```

Do not keep a Vercel request open for thousands of simulations.

Job states: `QUEUED` · `RUNNING` · `COMPLETED` · `FAILED`

---

## 22. Storage

Hackathon:

- Local JSON / object artifacts in development  
- Object storage / HF dataset repo for large trajectories  
- Supabase/Postgres for metadata if time allows  

| What | Where |
|------|-------|
| Metadata | Supabase / Postgres |
| Trajectories / video | Object storage / HF datasets |
| Checkpoints | Hugging Face Hub |
| Benchmark configs | GitHub + DB metadata |

Do not push thousands of videos through the Vercel app server.

---

## 23. Hugging Face’s role

Use HF for: pretrained models, checkpoints, datasets, optional managed inference, LeRobot-compatible data.

Do **not** make HF the primary custom backend unless faster than Modal during implementation.

```
Modal → HF model / endpoint → Recovery adapter
```

Frontend never knows whether the model came from HF, Reactor, Modal, or a local checkpoint.

---

## 24. Model provider strategy

| Provider | Role |
|----------|------|
| `SmolVLAProvider` (default) | Zero-shot baseline + fine-tuned recovery |
| `WAMProvider` (optional) | World-model counterfactuals / sim; recovery plan if actions exist |
| `OpenVLAProvider` (optional) | Comparison baseline |
| `CustomerPolicyProvider` (future) | Arbitrary customer policy |

Product stays model-agnostic.

---

## 25. Recommended foundation-model experiment

Run this first:

1. **Model A:** SmolVLA pretrained / zero-shot  
2. **Model B:** SmolVLA fine-tuned on recovery trajectories  

Dataset: ~5k–20k episodes if budget permits — high diversity, short recovery trajectories. Do not chase “10k” for its own sake.

Good shape: 8 failure families × severity bands × timing bands × object/target configs × seeds × compositions. Episode count is secondary to diversity.

---

## 26. Learned policy output space

Prefer short action chunks and/or hierarchical recovery:

```
Language + image + state + recent history
                    ↓
             SmolVLA recovery model
                    ↓
             short action chunk
                    ↓
            low-level controller
```

Store alongside targets: failure type, recovery primitive, expert score, success/failure — enables later research on primitive selection, chunk prediction, direct VLA recovery, planner+VLA hybrids.

---

## 27. Hybrid recovery system

```
Failure → Detector → Policy selector
              ┌───────┼────────┐
           Rules   Learned   Foundation
              └───────┼────────┘
                      ↓
              Safety constraints
                      ↓
                   Execute → Verify
```

Rules act as safety fallback. A VLA must not invent arbitrary unsafe motions.

---

## 28. Safety layer

Every proposed recovery action passes a deterministic gate in the MVP:

- workspace / velocity bounds  
- collision checks / forbidden zones  
- max action duration  
- safe-stop trigger  

```
VLA proposes → safety validator → ALLOW / MODIFY / REJECT
```

---

## 29. Customer policy abstraction

Customers eventually provide: policy endpoint/checkpoint, observation schema, action schema, embodiment metadata, reset.

```python
class PolicyAdapter:
    observation_space
    action_space

    def reset(self, task): ...
    def act(self, observation, instruction): ...
```

RecoveryGym **wraps** the customer policy; it does not modify it.

---

## 30. What counts as successful recovery?

Not “robot moved somewhere reasonable.” Evaluator checks the **original task predicate**.

```python
success = (
    object_in_target
    and object_stable
    and robot_safe
)
```

Recovery success =

```
failure occurred
  AND system returned to a state from which
  original task completion was achieved
```

---

## 31. Run-level event logging

Every episode emits an event stream that powers the frontend timeline:

```json
{"t": 42, "event": "FAILURE_DETECTED", "failure_type": "OBJECT_SLIP", "confidence": 0.94}
{"t": 43, "event": "RECOVERY_STARTED", "policy": "RULE_RECOVERY"}
{"t": 71, "event": "RECOVERY_VERIFIED", "success": true}
```

---

## 32. Frontend demo flow

1. **Known failure** — inject `OBJECT_SLIP` → detect → rule recover  
2. **Random failure** — stress test → identify → recover  
3. **Model comparison** — Rule vs ML vs SmolVLA zero-shot vs fine-tuned  
4. **Customer report** — real report, not just another sim animation  

Deterministic first, then stochastic.

---

## 33. Vercel / v0 plan

Use v0 only to accelerate UI scaffolding. Prompt shape:

> Build a robotics reliability dashboard called RecoveryGym — make your robot sweat.
> Dark technical interface. Main simulator panel. Failure injection controls. Live event timeline. Recovery plan card. Recovery score card. Benchmark comparison charts. Stress-test configuration panel. Model/policy selector.

Wire to API manually. Do **not** ask v0 for simulation engine or model serving.

---

## 34. Deployment topology

```
GitHub
 │
 ├──────────────→ Vercel → Frontend
 │
 └──────────────→ Modal
                      │
              API · Workers · Training
                      │
              Reactor/WAM · HF / object storage
```

| Machine | Role |
|---------|------|
| M3 Air | Dev, local tests, frontend, debugging |
| Modal | Sim batches, model exec, training, long jobs |
| Vercel | Frontend, request handling / auth if added |
| HF | Models, datasets, checkpoints |

Never rely on the developer laptop as part of the deployed system.

---

## 35. Compute budget strategy

Treat ~550k Reactor credits as scarce. Priority:

1. Validate WAM/Reactor on one task  
2. Small high-quality counterfactual dataset  
3. Scale scenario diversity  
4. Generate recovery training dataset  
5. Final evaluation  

Modal GPU: foundation inference + fine-tune + large batches.  
M3 CPU: local sim, frontend, API, deterministic tests.

---

## 36. Failure generation algorithm

```python
class FailureGenerator:
    def sample(self, base_context, rng) -> FailureEvent: ...
    def apply(self, state, failure_event): ...
```

Generators: `ObjectSlip` · `GraspMiss` · `TargetShift` · `ActuatorNoise` · `SensorNoise` · `Occlusion` · `Obstacle` · `Composite` (samples N components into one combined event).

---

## 37. Scenario reproducibility

Every benchmark run records:

`benchmark_id` · `scenario_id` · `seed` · world-model version · policy version · failure-generator version · recovery-policy version · simulation config

Required for meaningful before/after comparisons.

---

## 38. Version everything

A result is only valid relative to policy, scenario generator, simulation, and recovery policy versions. Use git commit hashes and model IDs in reports, e.g.:

```
Policy: customer/policy-v3
Scenario generator: recoverygym@8e41c2a
Recovery policy: smolvla-recovery-v1
World model: reactor/wam/<version>
```

---

## 39. Security and customer isolation

Do not execute arbitrary customer model code in the API process.

Hackathon: HF model ID · known endpoint · pre-approved adapter. Later: sandboxed workers for containers.

Never run user-provided code with unrestricted credentials.

---

## 40. Caching

Cache counterfactuals by hash of:

`environment_config` · `initial_state` · `policy_version` · `failure_event` · `world_model_version` · `seed`

Reuse identical experiments.

---

## 41. Cost controls

Every benchmark supports: max episodes · max model calls · max WAM calls · max GPU time · max runtime.

| Profile | Episodes |
|---------|----------|
| Quick | 100 |
| Standard (default) | 1,000 |
| Deep | 10,000 |

Default demo mode stays cheap.

---

## 42. Observability

Structured JSON logs for: progress, failure distribution, model latency, world-model calls, training state, policy failures, exceptions. Do not rely only on print statements.

---

## 43. What NOT to build tonight

- General robotics OS  
- Multi-tenant auth/billing  
- Kubernetes  
- Arbitrary Docker upload pipeline  
- Full physical 3D sim from scratch  
- End-to-end VLA training from scratch  
- RL from scratch / DAgger before baseline works  
- 20+ tasks / 30+ failure categories  
- Real robot control unless hardware is already available  

Architecture can support these later.

---

## 44. Hackathon implementation order

| Phase | Time | Goal | Acceptance |
|-------|------|------|------------|
| 0 | 30–45m | Repo: `apps/web`, `services/api`, `packages/core`, `packages/schemas`; GitHub / Vercel / Modal / env | Project boots |
| 1 | 60–90m | Local pick-and-place sim | Nominal policy succeeds repeatedly |
| 2 | 60m | Deterministic failure engine | Known failures reproduce from seed |
| 3 | 60m | Stochastic perturbations | Same family → varied timing/severity/outcomes |
| 4 | 60–90m | Rule recovery + evaluator | ≥3 failure families recover |
| 5 | 45–60m | Metrics + OOD split | Honest baseline comparison |
| 6 | 60–90m | Reactor/WAM | One counterfactual path works |
| 7 | 60–90m | Frontend (v0/Vercel) | Judge runs scenario without terminal |
| 8 | Remaining | SmolVLA experiment if infra works | **Do not risk working demo for a model** |

**Priority rule:** never sacrifice the working benchmark/demo to add another model.

---

## 45. Minimum viable learned-recovery experiment

If only one learning experiment:

1. Generate high-diversity failure/recovery trajectories  
2. Export training dataset  
3. Fine-tune SmolVLA (or compact pretrained VLA)  
4. Evaluate on held-out OOD suite  
5. Compare zero-shot vs fine-tuned  

Goal: show that counterfactual recovery trajectories can adapt a pretrained robot foundation model toward recovery behavior — not SOTA.

---

## 46. If foundation-model fine-tuning fails

Submission is still valid. Fall back to:

**Rule recovery + failure dataset generation + WAM/Reactor counterfactuals + robustness benchmark**

Show planned foundation-model pipeline as next stage. **Do not fabricate learning results.**

---

## 47. Research experiment matrix

| | Known | Random | OOD | Composite |
|--|:-----:|:------:|:---:|:---------:|
| No recovery | ✓ | ✓ | ✓ | ✓ |
| Rule recovery | ✓ | ✓ | ✓ | ✓ |
| ML baseline | ✓ | ✓ | ✓ | ✓ |
| Zero-shot VLA | ✓ | ✓ | ✓ | ✓ |
| Fine-tuned VLA | ✓ | ✓ | ✓ | ✓ |

**Hypothesis:** Fine-tuning on diverse counterfactual recovery trajectories improves recovery over zero-shot VLA; OOD/compositional performance reveals whether the model learned recovery or memorized failure templates.

---

## 48. What would make this impressive

Strongest result is **not** “our simulator generates failures.”

It is:

> We took a pretrained robot foundation model, stress-tested it on thousands of stochastic and compositional failures, generated corrective demonstrations, fine-tuned a recovery policy, and measured an improvement on held-out novel failures.

Modest honest gains beat fake 99% scores. Use only actual measurements.

---

## 49. Longer-term product roadmap

| Version | Focus |
|---------|--------|
| **V0 — Hackathon** | 1 task · 6–8 failures · rule recovery · stochastic gen · WAM/Reactor · SmolVLA experiment · frontend |
| **V1 — Research prototype** | 5–10 tasks · multi-embodiment · better taxonomy · learned detector · recovery FM · OOD bench |
| **V2 — Customer alpha** | Policy upload/adapters · custom scenarios · batch eval · reports · dataset export |
| **V3 — Recovery platform** | Fine-tune jobs · DAgger/relabel · active failure gen · adversarial stress · cross-embodiment · real-robot replay |
| **V4 — Continuous reliability** | Policy registry · continuous eval · regression · version compare · failure DB · recovery model marketplace |

---

## 50. Suggested repository structure

```
recoverygym/
├── apps/
│   └── web/                 # Next.js frontend
├── services/
│   └── api/                 # FastAPI on Modal
├── packages/
│   ├── core/                # sim, failures, detection, recovery, evaluation
│   ├── policies/            # adapters (rule, learned, smolvla, wam)
│   └── schemas/             # task, failure, trajectory, benchmark
├── training/
│   ├── datasets/
│   ├── export/
│   ├── configs/
│   └── scripts/
├── experiments/
│   ├── configs/
│   └── results/
├── docs/
├── README.md
├── plan.md
└── pyproject.toml
```

Start smaller if needed. **Boundaries matter more than directory count.**

---

## 51. Implementation milestones (smoke-test gated)

Do not advance until the previous milestone has a working smoke test.

| # | Milestone | Smoke tests |
|---|-----------|-------------|
| 1 | Local deterministic env | Nominal pass; reset deterministic; seeded failure deterministic |
| 2 | Stochastic failure generator | Same seed → same scenario; new seed → varied outcomes; params logged |
| 3 | Recovery primitives + rules | Failure → expected plan; plan executes; verification works |
| 4 | Benchmark evaluator | Metrics correct; train/test/OOD no overlap; result reproducible |
| 5 | Modal API | `POST /runs`, `POST /benchmarks`, `GET /benchmarks/{id}` |
| 6 | Vercel frontend | Run scenario; see failure, recovery, score |
| 7 | Reactor/WAM adapter | One counterfactual; artifact stored; metadata linked |
| 8 | SmolVLA inference | Zero-shot adapter executes; actions normalized |
| 9 | Fine-tuning pipeline | Dataset exports; job starts; checkpoint saved & evaluable |

---

## 52. Definition of done (hackathon)

A judge can do this in **under 2 minutes**, no terminal / local Python / manual JSON:

1. Select a robot policy  
2. Select pick-and-place  
3. Click **Stress Test**  
4. Watch a failure appear  
5. See the failure classified  
6. See the recovery plan  
7. Watch the robot recover  
8. See baseline vs recovery metrics  
9. See the generated corrective dataset  
10. See the foundation-model fine-tuning path / result if completed  

---

## 53. Final positioning

**RecoveryGym** — *make your robot sweat.*

Not: “a robot that can recover.”  
Yes: **a complete robot gym** for robustness and recovery evaluation.

**Long-term promise:**

> Upload a policy. Break it thousands of different ways. Measure where it fails. Generate corrective experience. Fine-tune recovery. Re-test.

**Moat (if it becomes a company):** not the simulator UI, but the combination of

failure generation + taxonomy + large-scale counterfactual evaluation + recovery trajectories + OOD evaluation + recovery-policy training + policy/model-agnostic infrastructure.

---

## 54. Immediate next actions

1. Create the repo and core interfaces  
2. Build the simplest working pick-and-place environment  
3. Implement deterministic + stochastic failure events  
4. Implement 5 recovery primitives and 3 rule-based policies  
5. Implement the evaluator and OOD split  
6. Build the first Modal endpoint  
7. Connect Vercel frontend  
8. Integrate Reactor/WAM for one counterfactual path  
9. Generate the first recovery dataset  
10. Run a small SmolVLA zero-shot + fine-tune experiment  

Only after all of that: more failure classes / tasks.

**Priority rule: never sacrifice the working benchmark/demo to add another model.**
