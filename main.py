import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import ValidationError

from services.vlogger_script_engine import (
    VloggerScriptRequest,
    VloggerScriptResponse,
    generate_vlogger_script,
)

app = FastAPI(title="VlogSpark AI Backend", version="2.1.0")

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "engine": "natural-human-vlogger-script-engine",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
    }


@app.get("/")
async def serve_frontend():
    index_path = Path(__file__).resolve().parent.parent / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_path)


@app.post("/api/generate-content", response_model=VloggerScriptResponse)
async def generate_content(req: VloggerScriptRequest):
    try:
        return generate_vlogger_script(req)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI returned an invalid response structure: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API request failed: {exc}",
        ) from exc
