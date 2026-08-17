import sqlite3
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.scam_rules import run_rules
from app.ai_provider import explain_risk, AIUnavailable
from app.schemas import ScanRequest, ScanResponse

DB_PATH = Path(__file__).resolve().parent.parent / "trust_checker.db"

app = FastAPI(title="AI Trust Checker API", version="0.1.0")

# Wide-open CORS: this is a local dev server talked to by the Expo app over
# your LAN / Expo Go tunnel. Tighten this before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at REAL NOT NULL
        )
        """
    )
    return conn


def score_to_level(score: int) -> str:
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


DEFAULT_ACTIONS = {
    "HIGH": [
        "Do not click any links in this message",
        "Do not share OTP, PIN, or passwords",
        "Verify directly through the official app or website",
    ],
    "MEDIUM": [
        "Be cautious before acting on this message",
        "Verify the sender through an official channel",
    ],
    "LOW": [
        "No strong red flags found, but stay alert with unfamiliar senders",
    ],
}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=ScanResponse)
async def analyze(req: ScanRequest):
    text = req.text.strip()
    rules = run_rules(text)

    score = rules.base_score
    category = rules.category
    confidence = "medium"
    summary = ""
    red_flags = [h.label for h in rules.hits]
    actions = DEFAULT_ACTIONS[score_to_level(score)]
    ai_used = False
    ai_error = None

    try:
        ai_result = await explain_risk(text, rules.hits, category, score)
        adj = int(ai_result.get("score_adjustment", 0) or 0)
        adj = max(-20, min(20, adj))
        score = max(0, min(100, score + adj))
        category = ai_result.get("category") or category
        confidence = ai_result.get("confidence", confidence)
        summary = ai_result.get("summary", "")
        ai_actions = ai_result.get("recommended_actions") or []
        if ai_actions:
            actions = ai_actions
        ai_used = True
    except AIUnavailable as e:
        ai_error = str(e)
        if not red_flags:
            summary = "No strong scam/phishing patterns detected by the rule engine. AI reasoning was unavailable, so treat this as a partial check."
            confidence = "low"
        else:
            summary = f"Rule-based patterns detected: {', '.join(red_flags[:3])}. AI reasoning was unavailable, so this is a partial check."
            confidence = "medium"

    level = score_to_level(score)

    conn = get_db()
    conn.execute(
        "INSERT INTO scans (text, risk_score, risk_level, category, created_at) VALUES (?, ?, ?, ?, ?)",
        (text, score, level, category, time.time()),
    )
    conn.commit()
    conn.close()

    return ScanResponse(
        risk_score=score,
        risk_level=level,
        confidence=confidence,
        category=category,
        red_flags=red_flags,
        recommended_actions=actions,
        summary=summary,
        ai_used=ai_used,
        ai_error=ai_error,
    )


@app.get("/history")
def history(limit: int = 20):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, text, risk_score, risk_level, category, created_at FROM scans ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "text": r[1][:120],
            "risk_score": r[2],
            "risk_level": r[3],
            "category": r[4],
            "created_at": r[5],
        }
        for r in rows
    ]
