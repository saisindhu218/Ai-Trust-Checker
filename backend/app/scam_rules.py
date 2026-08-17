"""
Rule-based scam/phishing signal engine.

This runs FIRST, before any AI call, so the app still works (in a degraded
mode) if the AI API is down, rate-limited, or the user has no internet.
It's also what makes the AI reasoning step cheap: we only need the model
to explain/confirm, not to detect from scratch.
"""

import re
from dataclasses import dataclass, field


@dataclass
class RuleHit:
    label: str
    weight: int  # contribution to risk score, 0-100 scale of importance


@dataclass
class RuleResult:
    hits: list = field(default_factory=list)
    category: str = "Unknown"
    base_score: int = 0

    def add(self, label: str, weight: int):
        self.hits.append(RuleHit(label=label, weight=weight))
        self.base_score = min(100, self.base_score + weight)


# Each pattern: (regex, label shown to user, weight, category if this fires)
PATTERNS = [
    (r"\b(otp|one[\s-]?time password)\b.{0,40}\b(share|send|tell|enter)\b", "Asks you to share an OTP", 30, "Phishing / Account Takeover"),
    (r"\b(account|kyc|card)\b.{0,30}\b(block|suspend|freeze|deactivat)\w*\b", "Threatens to block/suspend your account", 22, "Phishing / Impersonation"),
    (r"\b(click|tap)\b.{0,20}\b(link|here|below|now)\b", "Urges you to click a link immediately", 15, "Phishing / Impersonation"),
    (r"\bwithin\s+(\d+)\s*(hour|hr|minute|min)s?\b", "Creates a tight time pressure deadline", 15, "Phishing / Impersonation"),
    (r"\b(congratulation|winner|won|lucky draw|lottery)\b", "Claims you've won something unexpectedly", 25, "Lottery / Prize Scam"),
    (r"\b(pay|deposit|transfer)\b.{0,30}\b(processing fee|registration fee|customs|advance)\b", "Asks for an upfront/advance payment", 28, "Advance-Fee Scam"),
    (r"\b(work from home|earn.{0,15}(per day|daily)|part[\s-]?time job)\b.{0,30}\b(no experience|guaranteed)\b", "Job offer with unrealistic guarantees", 20, "Job Scam"),
    (r"\b(guaranteed|assured)\b.{0,20}\b(return|profit|income)\b", "Promises guaranteed investment returns", 28, "Investment Scam"),
    (r"\b(courier|parcel|package)\b.{0,30}\b(customs|held|seized|duty)\b", "Fake courier/customs detention story", 22, "Courier Scam"),
    (r"\b(police|cyber cell|cbi|income tax)\b.{0,30}\b(case|fir|warrant|notice)\b.{0,30}\b(pay|fine|settle)\b", "Impersonates law enforcement demanding payment", 30, "Government Impersonation"),
    (r"\b(upi|paytm|phonepe|gpay|google pay)\b.{0,20}\b(collect request|approve|accept)\b", "Asks you to approve a UPI collect request", 24, "UPI Scam"),
    (r"\b(pan|aadhaar|adhaar)\b.{0,20}\b(update|verify|link|expire)\b", "Fake KYC/ID document update request", 20, "Government Impersonation"),
    (r"\b(dear customer|dear user|valued customer)\b", "Generic greeting instead of your real name", 8, None),
    (r"(http[s]?://)?(bit\.ly|tinyurl|t\.co|is\.gd|goo\.gl)\S*", "Uses a shortened/obscured link", 12, None),
    (r"\b(loan)\b.{0,20}\b(instant|pre[\s-]?approved|no documents?)\b", "Instant no-document loan offer", 18, "Loan App Scam"),
]

URGENCY_WORDS = ["urgent", "immediately", "asap", "act now", "final notice", "last chance", "expire"]


def run_rules(text: str) -> RuleResult:
    result = RuleResult()
    lowered = text.lower()

    for pattern, label, weight, category in PATTERNS:
        if re.search(pattern, lowered):
            result.add(label, weight)
            if category and result.category == "Unknown":
                result.category = category

    urgency_hits = sum(1 for w in URGENCY_WORDS if w in lowered)
    if urgency_hits:
        result.add(f"Uses urgency/pressure language ({urgency_hits} signal(s))", min(15, urgency_hits * 5))

    if result.category == "Unknown" and result.hits:
        result.category = "Suspicious Content"

    return result
