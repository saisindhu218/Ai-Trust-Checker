import sqlite3
import time
import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.analyzer import analyze_text
from app.schemas import ScanRequest, ScanResponse

DB_PATH = Path(__file__).resolve().parent.parent / "trust_checker.db"

app = FastAPI(title="AI Trust Checker API", version="0.1.0")

API_ACCESS_TOKEN = os.environ.get("API_ACCESS_TOKEN", "").strip()
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]


def require_api_access(x_api_key: str | None = Header(default=None)) -> None:
    if API_ACCESS_TOKEN and x_api_key != API_ACCESS_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API key")

# Wide-open CORS: this is a local dev server talked to by the Expo app over
# your LAN / Expo Go tunnel. Tighten this before any public deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
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


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=ScanResponse, dependencies=[Depends(require_api_access)])
async def analyze(req: ScanRequest):
    text = req.text
    result = await analyze_text(text)

    conn = get_db()
    conn.execute(
        "INSERT INTO scans (text, risk_score, risk_level, category, created_at) VALUES (?, ?, ?, ?, ?)",
        (text, result["risk_score"], result["risk_level"], result["category"], time.time()),
    )
    conn.commit()
    conn.close()

    return ScanResponse(
        **result,
    )


@app.get("/history", dependencies=[Depends(require_api_access)])
def history(limit: int = Query(default=20, ge=1, le=100)):
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
