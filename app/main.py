from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.scrape import scrape_player, scrape_premier_only

app = FastAPI(title="CSStats Live API", version="1.0.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/player/{steam_id}/summary")
def player_summary(steam_id: str):
    try:
        data = scrape_player(steam_id)
        if not data.get("kd") and not data.get("csficacao") and not data.get("faceit_level"):
            raise HTTPException(status_code=502, detail="Could not extract data from csstats")
        return JSONResponse(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"internal_error: {e.__class__.__name__}")

@app.get("/premier/{steam_id}")
def premier(steam_id: str):
    try:
        return JSONResponse(scrape_premier_only(steam_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"internal_error: {e.__class__.__name__}")
