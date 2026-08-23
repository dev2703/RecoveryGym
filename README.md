# RecoveryGym

Make your robot sweat.

Stress-test a robot policy: inject failures, detect them, recover, score, and export corrective data.

## Status

| Done | Not done |
|------|----------|
| Local pick-and-place sim | Real MuJoCo / 3D physics |
| 8 failure types, deterministic + stochastic | Real Reactor/WAM API (mock only) |
| Predictive detector, rule recovery | Real SmolVLA GPU fine-tune |
| Recovery as a swappable seam | Learned (MLP) recovery baseline |
| Evaluation suite with held-out OOD split | Deployed Modal / Vercel |
| FastAPI + async benchmarks | Multi-task / multi-embodiment |
| Playground + report UI | Customer policy upload |
| Corrective dataset export, method comparison | |

Measured comparison is produced by real rollouts. No numbers are hard-coded, and
the SmolVLA adapters are labelled as structural placeholders until a checkpoint
is wired in.

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# API
uvicorn services.api.main:app --reload --port 8000

# UI (separate terminal)
cd apps/web && npm install && npm run dev
```

Open http://localhost:3000/playground

## Test

```bash
pytest tests/ -v            # all
pytest tests/unit -v        # unit
pytest tests/feature -v     # feature
```

## Packages

| Path | Role |
|------|------|
| `packages/schemas` | Task, failure, trajectory, episode, benchmark models |
| `packages/core/simulator` | Kinematic pick-and-place environment |
| `packages/core/failures` | Failure generators and injection |
| `packages/core/detection` | Predictive failure detector |
| `packages/core/recovery` | Recovery primitives, rule policy, safety gate |
| `packages/core/scenario` | Episode loop |
| `packages/core/evaluation` | Suite, splits, scoring |
| `packages/core/dataset` | Corrective dataset records |
| `packages/core/sim` | World model provider (WAM) |
| `packages/policies` | Nominal and SmolVLA adapters |
| `services/api` | FastAPI, job store, Modal entry |
| `apps/web` | Next.js playground and reports |
| `training` | SmolVLA fine-tune entry point |

## API

| Method | Path |
|--------|------|
| GET | `/health` |
| POST | `/v1/runs` |
| POST | `/v1/benchmarks` |
| GET | `/v1/benchmarks/{id}` |
| POST | `/v1/policies` |
| POST | `/v1/datasets/{id}/generate` |
| POST | `/v1/experiments/compare` |
| POST | `/v1/training` |
