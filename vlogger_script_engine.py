import json
import os
from typing import List

import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError


class VloggerScriptRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    platform: str = Field(default="YouTube Shorts", max_length=60)
    language: str = Field(default="English", max_length=40)
    content_type: str = Field(default="Daily Vlogger", max_length=60)
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
    editing_transition: str = "Smooth cut / J-cut into next clip"
    visual_prompt: str


class CaptionItem(BaseModel):
    label: str
    text: str


class VloggerScriptResponse(BaseModel):
    title: str
    platform: str
    language: str
    content_type: str
    tone: str
    duration: str
    audience: str
    source_mode: str = "live_ai"
    three_hooks: List[str]
    hook: str
    intro: str
    talking_points: List[str]
    example_story: str
    full_script: str
    voiceover: str
    strong_ending_cta: str
    speaking_guide: List[SpeakingCue]
    scenes: List[SceneItem]
    captions: List[CaptionItem]
    hashtags: str
    music_mood: str
    srt_preview: str
    lang_note: str


STYLE_GUIDANCE = {
    "Travel Vlogger": "Energetic, curious, observational; describe sights and logistics naturally without claiming you personally visited places you haven't.",
    "Daily Vlogger": "Warm, intimate, like chatting with a close friend on FaceTime; casual reactions and relatable everyday moments.",
    "Tech Vlogger": "Clear, honest, practical; explain specs in plain language like helping a friend pick a gadget, zero corporate buzzwords.",
    "Educational Creator": "Approachable, encouraging, step-by-step; use simple analogies and friendly check-ins with the viewer.",
    "Food Vlogger": "Sensory, enthusiastic, mouth-watering descriptions in simple everyday words; focus on texture, aroma, and honest reactions.",
    "Lifestyle Creator": "Calm, aesthetic, thoughtful; reflective pacing with gentle transitions and relatable habits.",
}


def generate_vlogger_script(req: VloggerScriptRequest) -> VloggerScriptResponse:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured on the server.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    style_note = STYLE_GUIDANCE.get(
        req.content_type,
        "Conversational, authentic, human-first delivery suitable for speaking comfortably on camera.",
    )

    prompt = f"""
You are VlogSpark AI's Natural Human Vlogger Script Engine.
Write an ORIGINAL video script and production plan that sounds like a real human vlogger speaking naturally to their camera and audience.

STRICT ANTI-AI-SLOP & HONESTY RULES:
1. NEVER sound like an essay, news report, advertisement, or formal AI article.
2. Use casual introductions, simple everyday vocabulary, short-to-medium spoken sentences, natural reactions, and friendly audience interaction.
3. NEVER use clichés like "In today's fast-paced world", "delve into", "unlock", "game-changer", or "tapestry".
4. NEVER invent personal experiences or claim the creator actually visited a place or did something they didn't. Frame examples honestly.
5. Every script must be 100% original and must NEVER copy any existing YouTuber's script or catchphrases.
6. Language rules for {req.language}:
   - If "Tanglish": natural Tamil + English conversational mix written in readable Latin script (the way Tamil creators actually speak on camera).
   - If Telugu, Tamil, Hindi, Kannada, or Malayalam: natural everyday spoken style with realistic English code-mixing for modern/tech terms (no stiff textbook translation).

Vlogger Style ({req.content_type}): {style_note}
Inputs:
- Topic/Title: {req.title}
- Platform: {req.platform}
- Language: {req.language}
- Duration: {req.duration}
- Audience: {req.audience}
- Speaking Tone: {req.tone}
- Variation Seed: {req.variation}

Return ONLY valid JSON with this exact schema:
{{
  "three_hooks": ["Hook 1 (Question)", "Hook 2 (Relatable moment)", "Hook 3 (Direct/honest opener)"],
  "hook": "Best single opening hook string",
  "intro": "Casual vlogger intro",
  "talking_points": ["Point 1", "Point 2", "Point 3"],
  "example_story": "Spontaneous relatable example (no invented personal claims)",
  "full_script": "Complete spoken-aloud script with natural pauses and reactions",
  "voiceover": "Natural voiceover narration",
  "strong_ending_cta": "Warm, natural ending and call to action",
  "speaking_guide": [
    {{"line": "string", "how": "string", "pause": "string", "emphasis": "string", "expression": "string", "speed": "string"}}
  ],
  "scenes": [
    {{"num": 1, "time": "0-8s", "shot": "string", "camera": "string", "line": "string", "on_screen": "string", "broll": "string", "editing_transition": "string", "visual_prompt": "string"}}
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
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )
    raw = json.loads(response.text)
    if not raw.get("hook") and raw.get("three_hooks"):
        raw["hook"] = raw["three_hooks"][0]
    return VloggerScriptResponse(
        title=req.title,
        platform=req.platform,
        language=req.language,
        content_type=req.content_type,
        tone=req.tone,
        duration=req.duration,
        audience=req.audience,
        source_mode="live_ai",
        **raw,
    )
