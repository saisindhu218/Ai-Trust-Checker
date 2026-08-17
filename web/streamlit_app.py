"""
AI Trust Checker — Streamlit web version.

Reuses the SAME rule engine and Gemini wrapper as the mobile app's backend
(imported directly from ../backend/app), so scam-detection logic only lives
in one place. This does not require the FastAPI server to be running —
Streamlit talks to the rule engine and Gemini directly.

Run with:  streamlit run streamlit_app.py
"""

import asyncio
import os
import sys
from pathlib import Path

import streamlit as st

# Make the backend package importable: web/ -> ../backend
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.scam_rules import run_rules          # noqa: E402
from app.ai_provider import explain_risk, AIUnavailable  # noqa: E402

st.set_page_config(page_title="AI Trust Checker", page_icon="🛡️", layout="centered")

LEVEL_COLOR = {"HIGH": "#DC2626", "MEDIUM": "#D97706", "LOW": "#16A34A"}

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
    "LOW": ["No strong red flags found, but stay alert with unfamiliar senders"],
}


def score_to_level(score: int) -> str:
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def analyze(text: str) -> dict:
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
        ai_result = asyncio.run(explain_risk(text, rules.hits, category, score))
        adj = max(-20, min(20, int(ai_result.get("score_adjustment", 0) or 0)))
        score = max(0, min(100, score + adj))
        category = ai_result.get("category") or category
        confidence = ai_result.get("confidence", confidence)
        summary = ai_result.get("summary", "")
        actions = ai_result.get("recommended_actions") or actions
        ai_used = True
    except AIUnavailable as e:
        ai_error = str(e)
        if not red_flags:
            summary = "No strong scam/phishing patterns detected by the rule engine. AI reasoning was unavailable, so treat this as a partial check."
            confidence = "low"
        else:
            summary = f"Rule-based patterns detected: {', '.join(red_flags[:3])}. AI reasoning was unavailable, so this is a partial check."

    return {
        "risk_score": score,
        "risk_level": score_to_level(score),
        "confidence": confidence,
        "category": category,
        "red_flags": red_flags,
        "recommended_actions": actions,
        "summary": summary,
        "ai_used": ai_used,
        "ai_error": ai_error,
    }


st.title("🛡️ AI Trust Checker")
st.caption("Before you click, pay, share, or believe — check it.")

if not os.environ.get("GEMINI_API_KEY"):
    st.warning(
        "No GEMINI_API_KEY set — running in rule-based-only mode. "
        "Set it in web/.env or as an environment variable for AI-assisted reasoning.",
        icon="⚠️",
    )

text = st.text_area(
    "Paste a suspicious SMS, WhatsApp, or email message",
    height=150,
    placeholder="e.g. Your SBI account will be blocked today. Click this link immediately...",
)

if st.button("CHECK NOW", type="primary", use_container_width=True):
    if not text.strip():
        st.error("Paste a message first.")
    else:
        with st.spinner("Analyzing..."):
            result = analyze(text.strip())

        color = LEVEL_COLOR[result["risk_level"]]
        st.markdown(
            f"""
            <div style="border:2px solid {color}; border-radius:12px; padding:20px; text-align:center; margin-top:16px;">
                <div style="font-size:36px; font-weight:800; color:{color};">{result['risk_score']}/100</div>
                <div style="font-size:18px; font-weight:700; color:{color};">{result['risk_level']} RISK</div>
                <div style="font-size:14px; color:#475569; margin-top:4px;">{result['category']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if result["summary"]:
            st.write(result["summary"])

        if result["red_flags"]:
            st.subheader("Why we flagged this")
            for flag in result["red_flags"]:
                st.markdown(f"⚠ {flag}")

        st.subheader("What you should do")
        for i, action in enumerate(result["recommended_actions"], 1):
            st.markdown(f"{i}. {action}")

        st.caption(
            f"Confidence: {result['confidence'].upper()} · "
            f"{'AI-assisted' if result['ai_used'] else 'Rule-based only'}"
        )
        if result["ai_error"]:
            st.info(f"AI reasoning unavailable ({result['ai_error']}). Showing rule-based result only.")
