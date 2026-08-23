# RecoveryGym

Make your robot sweat.

Stress-test a robot policy: inject failures, detect them, recover, score, and export corrective data.

## Branches

| Branch | Purpose |
|--------|---------|
| `main` | Full monorepo — source of truth |
| `frontend` | Vercel production branch (`apps/web`) |
| `backend` | Modal + Hugging Face pipelines |

## Status

| Done | Notes |
|------|-------|
| Local pick-and-place sim + 8 failure types | Deterministic + stochastic |
| Rule recovery + evaluator + OOD splits | Real rollouts |
| FastAPI + async benchmarks | Local threads or Modal spawn |
| Reactor WAM integration | Set `REACTOR_API_KEY`, `USE_MOCK_WAM=false` |
| SmolVLA adapter | Loads LeRobot when `HF_TOKEN` + GPU available |
| Modal deployment | `modal deploy services/api/modal_app.py` |
| HF dataset export + LoRA pipeline | `training/export/lerobot.py` |
| Next.js playground + reports | Point at Modal via `NEXT_PUBLIC_API_URL` |

## Setup

```bash
cp .env.example .env
# Fill REACTOR_API_KEY, HF_TOKEN, HF_DATASET_REPO, HF_MODEL_REPO

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# API
uvicorn services.api.main:app --reload --port 8000

# UI
cd apps/web && npm install && npm run dev
```

Open http://localhost:3000/playground

## Modal (backend)

```bash
modal secret create recoverygym-secrets \
  REACTOR_API_KEY=... \
  HF_TOKEN=... \
  RECOVERYGYM_ARTIFACTS_DIR=/data/artifacts \
  USE_MOCK_WAM=false \
  SMOLVLA_ALLOW_FALLBACK=false \
  HF_DATASET_REPO=your-user/recoverygym-recovery \
  HF_MODEL_REPO=your-user/recoverygym-smolvla-recovery \
  REACTOR_MODEL_NAME=reactor/helios

modal volume create recoverygym-artifacts
modal deploy services/api/modal_app.py
```

Copy the deployed URL into Vercel as `NEXT_PUBLIC_API_URL`.

## Vercel (frontend branch)

1. Import GitHub repo in Vercel
2. **Production branch:** `frontend`
3. **Root directory:** `apps/web`
4. **Environment variable:** `NEXT_PUBLIC_API_URL=https://<workspace>--recoverygym-fastapi-app.modal.run`

## GitHub secrets (CI/CD)

| Secret | Used by |
|--------|---------|
| `MODAL_TOKEN_ID` | deploy-modal.yml |
| `MODAL_TOKEN_SECRET` | deploy-modal.yml |
| `HF_TOKEN` | hf-sync.yml |
| `HF_DATASET_REPO` | hf-sync.yml |
| `HF_MODEL_REPO` | hf-sync.yml |

## Test

```bash
pytest tests/ -v
```

## API

| Method | Path |
|--------|------|
| GET | `/health` |
| POST | `/v1/runs` |
| POST | `/v1/benchmarks` |
| GET | `/v1/benchmarks/{id}` |
| POST | `/v1/policies` |
| POST | `/v1/datasets/{id}/generate?push_to_hf=true` |
| POST | `/v1/training` |
| GET | `/v1/training/{id}` |
| POST | `/v1/experiments/compare` |
