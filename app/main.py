from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.scrape import scrape_player, scrape_premier_only, scrape_live_sample

app = FastAPI(title="CSStats Live API", version="1.0.0")

@app.get("/health")
def health():
    return {"ok": True}

# endpoint "clean" com kd, csficacao e faceit_level
@app.get("/player/{steam_id}/summary")
def player_summary(steam_id: str):
    try:
        data = scrape_player(steam_id)
        if not data.get("kd") and not data.get("csficacao") and not data.get("faceit_level"):
            raise HTTPException(status_code=502, detail="upstream_parse_error: could not extract data")
        return JSONResponse(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream_error: {e.__class__.__name__}")

# alias útil (você pode chamar só /player/{id} também)
@app.get("/player/{steam_id}")
def player_alias(steam_id: str):
    return player_summary(steam_id)

# rota premier-only (pra compatibilidade com o que você já chamava)
@app.get("/premier/{steam_id}")
def premier(steam_id: str):
    try:
        return JSONResponse(scrape_premier_only(steam_id))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream_error: {e.__class__.__name__}")

# rota live simples (se não usar, tudo bem)
@app.get("/player/{steam_id}/live")
def live(steam_id: str):
    try:
        return JSONResponse(scrape_live_sample(steam_id))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"upstream_error: {e.__class__.__name__}")
