# RecoveryGym

Make your robot sweat.

Stress-test a robot policy: inject failures, detect them, recover, score, and export corrective data.

## Setup

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# API
uvicorn services.api.main:app --reload --port 8000

# UI
cd apps/web && npm install && npm run dev
```

## Test

```
pytest tests/ -v
```


