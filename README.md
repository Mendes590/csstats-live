# CSStats Live API (clean)

FastAPI service that returns **KD**, **Premier rating (csficacao)**, and **Faceit level** for a CSStats player page.

## Endpoints

- `GET /health`
- `GET /player/{steam_id}/summary`
- `GET /premier/{steam_id}`

## Local dev

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install
uvicorn app.main:app --reload --port 8000
```

## Deploy to Koyeb (Buildpack)

1. Push to GitHub.
2. Create Web Service from the repo.
3. Builder: **Buildpack**.
4. Ports: TCP 8000 health check.
5. Deploy.
