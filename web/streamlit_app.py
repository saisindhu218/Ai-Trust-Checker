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

from app.analyzer import analyze_text  # noqa: E402

st.set_page_config(page_title="AI Trust Checker", page_icon="🛡️", layout="centered")

LEVEL_COLOR = {"HIGH": "#DC2626", "MEDIUM": "#D97706", "LOW": "#16A34A"}

def analyze(text: str) -> dict:
    try:
        return asyncio.run(analyze_text(text))
    except RuntimeError as error:
        if "asyncio.run() cannot be called" not in str(error):
            raise
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(analyze_text(text))
        finally:
            loop.close()


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
