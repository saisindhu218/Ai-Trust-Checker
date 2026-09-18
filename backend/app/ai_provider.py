"""
Thin wrapper around the Gemini free-tier API.

Kept as a separate module (not called directly from main.py's business logic)
so that swapping providers later (Groq, local model, etc.) only means adding
a new function here and changing one line in main.py.
"""

import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

from app.schemas import AIResult

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / "web" / ".env")
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# IMPORTANT: gemini-2.0-flash was RETIRED by Google on June 1, 2026 — any
# request to it now returns 404. gemini-2.5-flash is the current free-tier
# model as of August 2026, confirmed to run on the free tier with generous
# rate limits. Google has flagged 2.5-series models for retirement around
# Oct 16, 2026 — if this starts 404ing again after that date, swap the
# default below to whatever Google's current free-tier Flash model is
# (check https://ai.google.dev/gemini-api/docs/models for the live list).
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
)


class AIUnavailable(Exception):
    pass


async def explain_risk(text: str, rule_hits: list, category: str, base_score: int) -> dict:
    """
    Ask Gemini to REASON about content that the rule engine already flagged
    (or didn't flag), and return a short structured explanation.
    The rule engine — not the AI — owns the score, so a flaky AI response
    never wipes out risk detection.
    """
    if not GEMINI_API_KEY:
        raise AIUnavailable("No GEMINI_API_KEY set")

    hits_text = "\n".join(f"- {h.label}" for h in rule_hits) or "- (none matched by rule engine)"

    prompt = f"""You are a fraud/scam analyst assistant for an Indian consumer safety app.
A user submitted this message for a trust/risk check:

---
{text}
---

Automated pattern signals already detected:
{hits_text}

Preliminary category guess: {category}
Preliminary rule-based score (0-100, higher = riskier): {base_score}

Respond with ONLY a JSON object, no markdown, no backticks, in this exact shape:
{{
  "summary": "one or two plain-English sentences explaining the main risk (or why it looks fine)",
  "recommended_actions": ["short imperative action", "short imperative action", "..."],
  "confidence": "low" | "medium" | "high",
  "category": "short category name",
  "score_adjustment": integer from -20 to 20 (how much to adjust the base score, 0 if you agree with it)
}}

Be honest about uncertainty. Never claim 100% certainty either way. If this looks
like ordinary, safe content, say so plainly and keep the score low."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 800,
            "responseMimeType": "application/json",
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(GEMINI_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.removeprefix("```").removeprefix("json").strip()
                cleaned = cleaned.removesuffix("```").strip()
            if not cleaned.startswith("{"):
                cleaned = cleaned[cleaned.find("{") : cleaned.rfind("}") + 1]
            parsed = json.loads(cleaned)
            if not isinstance(parsed, dict):
                raise ValueError("Gemini response was not a JSON object")
            try:
                parsed["score_adjustment"] = max(-20, min(20, int(parsed.get("score_adjustment", 0))))
            except (TypeError, ValueError):
                parsed["score_adjustment"] = 0
            if isinstance(parsed.get("recommended_actions"), list):
                parsed["recommended_actions"] = parsed["recommended_actions"][:5]
            return AIResult.model_validate(parsed)
    except Exception as e:
        raise AIUnavailable(f"{type(e).__name__}: {e}")
