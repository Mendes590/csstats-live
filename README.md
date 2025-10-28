# CSStats Live API

Endpoints:
- `GET /health` -> {"ok": true}
- `GET /player/{steam_id}/summary` -> { kd, csficacao, faceit_level, ... }
- `GET /player/{steam_id}` -> alias de `/summary`
- `GET /premier/{steam_id}` -> só premier (compat)
- `GET /player/{steam_id}/live` -> sample (opcional)

## Local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install  # só se for rodar fora do Docker
uvicorn app.main:app --reload --port 8000
