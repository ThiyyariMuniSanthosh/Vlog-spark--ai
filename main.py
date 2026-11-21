import json
import os
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError
import google.generativeai as genai

app = FastAPI(title="VlogSpark AI Backend", version="2.0.0")

# Secure CORS configuration from environment variable
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ContentRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    platform: str = Field(default="YouTube Shorts", max_length=60)
    language: str = Field(default="English", max_length=40)
    content_type: str = Field(default="Educational", max_length=60)
    tone: str = Field(default="Casual & Conversational", max_length=80)
    duration: str = Field(default="60 sec", max_length=40)
    audience: str = Field(default="Students & Beginners", max_length=80)
    variation: int = Field(default=0, ge=0, le=100)


class SpeakingCue(BaseModel):
    line: str
    how: str
    pause: str
    emphasis: str
    expression: str
    speed: str


class SceneItem(BaseModel):
    num: int
    time: str
    shot: str
    camera: str
    line: str
    on_screen: str
    broll: str
    visual_prompt: str


class CaptionItem(BaseModel):
    label: str
    text: str


class GeneratedContentResponse(BaseModel):
    title: str
    platform: str
    language: str
    content_type: str
    tone: str
    duration: str
    audience: str
    source_mode: str = "live_ai"
    hook: str
    intro: str
    talking_points: List[str]
    example_story: str
    full_script: str
    voiceover: str
    speaking_guide: List[SpeakingCue]
    scenes: List[SceneItem]
    captions: List[CaptionItem]
    hashtags: str
    music_mood: str
    srt_preview: str
    lang_note: str


@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
    }


@app.get("/")
async def serve_frontend():
    index_path = Path(__file__).resolve().parent.parent / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="Frontend index.html not found.")
    return FileResponse(index_path)


@app.post("/api/generate-content", response_model=GeneratedContentResponse)
async def generate_content(req: ContentRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GEMINI_API_KEY is not configured on the server. Add it to your .env file and restart the backend.",
        )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = f"""
You are VlogSpark AI, a warm, natural human video content director.
Turn the user's title/topic into a ready-to-record production package.

CRITICAL WRITING RULES:
- Sound like a real person speaking comfortably to a camera, NOT a robotic AI article.
- Use short, natural spoken-aloud sentences and everyday conversational transitions.
- If Language is Telugu, Tamil, Hindi, Kannada, Malayalam, Marathi, or Bengali, write natural spoken regional phrasing with realistic code-mixing where appropriate (never stiff textbook translation).
- Variation seed: {req.variation} (if > 0, offer a fresh opening hook and angle).

Inputs:
- Title/Topic: {req.title}
- Platform: {req.platform}
- Language: {req.language}
- Content Type: {req.content_type}
- Tone: {req.tone}
- Duration: {req.duration}
- Target Audience: {req.audience}

Return ONLY valid JSON matching this exact structure:
{{
  "hook": "string",
  "intro": "string",
  "talking_points": ["string", "string", "string"],
  "example_story": "string",
  "full_script": "string",
  "voiceover": "string",
  "speaking_guide": [
    {{"line": "string", "how": "string", "pause": "string", "emphasis": "string", "expression": "string", "speed": "string"}}
  ],
  "scenes": [
    {{"num": 1, "time": "0-8s", "shot": "string", "camera": "string", "line": "string", "on_screen": "string", "broll": "string", "visual_prompt": "string"}}
  ],
  "captions": [
    {{"label": "Short & Punchy", "text": "string"}},
    {{"label": "Storytelling", "text": "string"}},
    {{"label": "Discussion Starter", "text": "string"}}
  ],
  "hashtags": "string",
  "music_mood": "string",
  "srt_preview": "string",
  "lang_note": "string"
}}
"""
    try:
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        raw_data = json.loads(response.text)
        validated = GeneratedContentResponse(
            title=req.title,
            platform=req.platform,
            language=req.language,
            content_type=req.content_type,
            tone=req.tone,
            duration=req.duration,
            audience=req.audience,
            source_mode="live_ai",
            **raw_data,
        )
        return validated
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
