from app.ai_provider import AIUnavailable, explain_risk
from app.scam_rules import run_rules


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


def score_to_level(score: int) -> str:
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


async def analyze_text(text: str) -> dict:
    rules = run_rules(text)
    score = rules.base_score
    category = rules.category
    confidence = "medium"
    summary = ""
    red_flags = [hit.label for hit in rules.hits]
    ai_used = False
    ai_error = None
    ai_actions = []

    try:
        ai_result = await explain_risk(text, rules.hits, category, score)
        # The deterministic engine is a safety floor; AI can add context but
        # must not downgrade strong rule-based scam evidence.
        score = max(0, min(100, score + max(0, ai_result.score_adjustment)))
        category = ai_result.category or category
        confidence = ai_result.confidence
        summary = ai_result.summary
        ai_actions = ai_result.recommended_actions
        ai_used = True
    except AIUnavailable:
        ai_error = "AI reasoning is unavailable"
        if not red_flags:
            summary = "No strong scam/phishing patterns detected by the rule engine. AI reasoning was unavailable, so treat this as a partial check."
            confidence = "low"
        else:
            summary = f"Rule-based patterns detected: {', '.join(red_flags[:3])}. AI reasoning was unavailable, so this is a partial check."

    level = score_to_level(score)
    actions = ai_actions or DEFAULT_ACTIONS[level]
    return {
        "risk_score": score,
        "risk_level": level,
        "confidence": confidence,
        "category": category,
        "red_flags": red_flags,
        "recommended_actions": actions,
        "summary": summary,
        "ai_used": ai_used,
        "ai_error": ai_error,
    }