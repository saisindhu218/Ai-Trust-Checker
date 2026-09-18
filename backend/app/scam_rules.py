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
    (r"\b(otp|one[\s-]?time password)\b.{0,50}\b(share|send|tell|enter|provide|submit|complete|verify)\b|\b(share|send|tell|enter|provide|submit|complete|verify)\b.{0,50}\b(otp|one[\s-]?time password)\b", "Asks you to share or enter an OTP", 30, "Phishing / Account Takeover"),
    (r"\b(atm\s+pin|debit\s+card\s+pin|pin)\b.{0,50}\b(enter|share|send|provide|submit|complete|verify)\b|\b(enter|share|send|provide|submit|complete|verify)\b.{0,50}\b(atm\s+pin|debit\s+card\s+pin|pin)\b", "Asks you to enter or share a PIN", 35, "Phishing / Account Takeover"),
    (r"\b(account|kyc|card)\b.{0,30}\b(block|suspend|freeze|deactivat)\w*\b", "Threatens to block/suspend your account", 22, "Phishing / Impersonation"),
    (r"\b(click(?:ing)?|tap(?:ping)?)\b.{0,40}\b(link|here|below|now)\b|\b(link|here|below)\b.{0,40}\b(click(?:ing)?|tap(?:ping)?)\b", "Urges you to click a link", 15, "Phishing / Impersonation"),
    (r"\b(click|tap|visit|open)\b.{0,50}https?://\S+", "Sends a link for verification or payment", 15, "Phishing / Impersonation"),
    (r"\bwithin\s+(\d+)\s*(hour|hr|minute|min)s?\b", "Creates a tight time pressure deadline", 15, "Phishing / Impersonation"),
    (r"\b(congratulation|winner|won|lucky draw|lottery)\b", "Claims you've won something unexpectedly", 25, "Lottery / Prize Scam"),
    (r"\b(pay|deposit|transfer)\b.{0,30}\b(processing fee|registration fee|customs|advance)\b", "Asks for an upfront/advance payment", 28, "Advance-Fee Scam"),
    (r"\b(work from home|earn.{0,15}(per day|daily)|part[\s-]?time job)\b.{0,30}\b(no experience|guaranteed)\b", "Job offer with unrealistic guarantees", 20, "Job Scam"),
    (r"\b(work from home|part[\s-]?time job|job offer|position)\b.{0,100}\b(pay|fee|deposit|registration)\b", "Job offer requires an upfront fee", 30, "Job Scam"),
    (r"\b(shortlisted|selected|salary)\b.{0,100}\b(pay|fee|registration)\b", "Job selection message requires an upfront fee", 30, "Job Scam"),
    (r"\b(guaranteed|assured)\b.{0,35}\b(return|profit|income)\b|\b(return|profit|income)s?\b.{0,60}\b(guaranteed|assured)\b", "Promises guaranteed investment returns", 28, "Investment Scam"),
    (r"\b(guaranteed|assured)\b.{0,70}\b(return|profit|income)s?\b", "Promises guaranteed investment returns", 28, "Investment Scam"),
    (r"\b(guaranteed|assured)\b.{0,80}\b(return|profit|income)s?\b.{0,80}\b(deposit|invest|transfer|pay)\b|\b(deposit|invest|transfer|pay)\b.{0,80}\b(guaranteed|assured)\b.{0,80}\b(return|profit|income)s?\b", "Combines guaranteed returns with an investment payment request", 25, "Investment Scam"),
    (r"\b(investment group|investing platform|trading platform)\b.{0,120}\b(profit|returns?)\b.{0,120}\b(start|join|deposit|invest)\b", "Investment promotion claims profits and urges you to join", 30, "Investment Scam"),
    (r"\b(courier|parcel|package)\b.{0,30}\b(customs|held|seized|duty)\b", "Fake courier/customs detention story", 22, "Courier Scam"),
    (r"\b(parcel|package|delivery)\b.{0,70}\b(address|redelivery|re-delivery|delivery)\b.{0,70}\b(charges?|fee|pay)\b", "Fake delivery address or redelivery fee request", 30, "Courier Scam"),
    (r"\b(police|cyber cell|cbi|income tax)\b.{0,30}\b(case|fir|warrant|notice)\b.{0,30}\b(pay|fine|settle)\b", "Impersonates law enforcement demanding payment", 30, "Government Impersonation"),
    (r"\b(upi|paytm|phonepe|gpay|google pay)\b.{0,20}\b(collect request|approve|accept)\b", "Asks you to approve a UPI collect request", 24, "UPI Scam"),
    (r"\b(pan|aadhaar|adhaar)\b.{0,20}\b(update|verify|link|expire)\b", "Fake KYC/ID document update request", 20, "Government Impersonation"),
    (r"\b(login|sign[\s-]?in)\b.{0,45}\b(new device|unusual|suspicious)\b.{0,100}\b(review|confirm|verify)\b.{0,60}https?://\S+", "Fake account security alert with a verification link", 35, "Phishing / Account Takeover"),
    (r"\b(electricity|power|utility)\b.{0,45}\b(disconnect|cut off|disconnection)\b", "Threatens electricity disconnection", 28, "Electricity Bill Scam"),
    (r"\b(bill|payment)\b.{0,45}\b(failed|pending|overdue|screenshot)\b", "Claims a bill payment problem and requests proof", 22, "Electricity Bill Scam"),
    (r"\b(pay|payment|transfer)\b.{0,50}https?://\S+", "Requests payment through a message link", 25, "Payment Scam"),
    (r"\b(send|share)\b.{0,25}(payment|transaction)\s+screenshot\b", "Requests a payment screenshot", 12, "Payment Scam"),
    (r"\b(lost|new)\s+(my\s+)?phone\b.{0,100}\b(urgent|emergency)\b", "Claims a relative has lost their phone and needs urgent help", 30, "Family Impersonation Scam"),
    (r"(?=.*\b(lost|new)\s+(my\s+)?phone\b)(?=.*\b(transfer|send|pay)\b.{0,60}\b(upi|money|₹|rs\.?\s*\d))", "Requests an urgent money transfer after a phone-loss claim", 25, "Family Impersonation Scam"),
    (r"(?=.*\b(lost|new)\s+(my\s+)?phone\b)\b(don['’]?t|do not)\s+(call|phone|contact)\b", "Pressures you not to verify by calling", 18, "Family Impersonation Scam"),
    (r"\b(dear customer|dear user|valued customer)\b", "Generic greeting instead of your real name", 8, None),
    (r"(http[s]?://)?(bit\.ly|tinyurl|t\.co|is\.gd|goo\.gl)\S*", "Uses a shortened/obscured link", 12, None),
    (r"\b(loan)\b.{0,20}\b(instant|pre[\s-]?approved|no documents?)\b", "Instant no-document loan offer", 18, "Loan App Scam"),
]

URGENCY_WORDS = ["urgent", "immediately", "asap", "act now", "final notice", "last chance", "expire"]

CATEGORY_PRIORITY = {
    "Phishing / Account Takeover": 100,
    "Family Impersonation Scam": 95,
    "Electricity Bill Scam": 90,
    "Investment Scam": 85,
    "Lottery / Prize Scam": 80,
    "Government Impersonation": 75,
    "Courier Scam": 70,
    "Job Scam": 65,
    "Loan App Scam": 60,
    "UPI Scam": 55,
    "Payment Scam": 50,
    "Advance-Fee Scam": 40,
    "Phishing / Impersonation": 30,
}


def run_rules(text: str) -> RuleResult:
    result = RuleResult()
    lowered = text.lower()

    for pattern, label, weight, category in PATTERNS:
        if re.search(pattern, lowered):
            result.add(label, weight)
            if category and result.category == "Unknown":
                result.category = category

    matched_categories = [
        category
        for pattern, label, weight, category in PATTERNS
        if category and re.search(pattern, lowered)
    ]
    if matched_categories:
        result.category = max(
            matched_categories,
            key=lambda category: CATEGORY_PRIORITY.get(category, 0),
        )

    urgency_hits = sum(1 for w in URGENCY_WORDS if w in lowered)
    if urgency_hits:
        result.add(f"Uses urgency/pressure language ({urgency_hits} signal(s))", min(15, urgency_hits * 5))

    if result.category == "Unknown" and result.hits:
        result.category = "Suspicious Content"

    # Multiple independent signals are strong evidence even when wording is unfamiliar.
    signal_names = {hit.label for hit in result.hits}
    if (
        "Threatens to block/suspend your account" in signal_names
        and "Asks you to share or enter an OTP" in signal_names
    ):
        result.add("Combines an account threat with a credential request", 25)
    if (
        result.category == "Investment Scam"
        and any("investment payment" in hit.label.lower() for hit in result.hits)
    ):
        result.add("Investment scam combination detected", 15)

    high_confidence_floors = [
        (
            result.category == "Phishing / Account Takeover"
            and any("account threat" in hit.label.lower() for hit in result.hits),
            80,
        ),
        (
            result.category == "Electricity Bill Scam"
            and any("payment" in hit.label.lower() for hit in result.hits),
            70,
        ),
        (
            result.category == "Family Impersonation Scam"
            and any("money transfer" in hit.label.lower() for hit in result.hits),
            70,
        ),
        (
            result.category == "Lottery / Prize Scam"
            and any("upfront" in hit.label.lower() for hit in result.hits),
            70,
        ),
        (
            result.category == "Investment Scam"
            and any("investment payment" in hit.label.lower() for hit in result.hits),
            70,
        ),
        (
            result.category == "Investment Scam"
            and any("investment promotion" in hit.label.lower() for hit in result.hits),
            70,
        ),
        (
            result.category == "Government Impersonation"
            and any("law enforcement" in hit.label.lower() for hit in result.hits),
            70,
        ),
        (
            result.category == "Courier Scam"
            and any("upfront" in hit.label.lower() for hit in result.hits),
            70,
        ),
        (
            result.category == "Courier Scam"
            and any("redelivery" in hit.label.lower() for hit in result.hits),
            65,
        ),
        (
            result.category == "Job Scam"
            and any("upfront" in hit.label.lower() for hit in result.hits),
            65,
        ),
        (
            result.category == "Job Scam"
            and any("job" in hit.label.lower() and "fee" in hit.label.lower() for hit in result.hits),
            65,
        ),
        (
            result.category == "Loan App Scam"
            and any("upfront" in hit.label.lower() for hit in result.hits),
            65,
        ),
        (
            result.category == "Phishing / Account Takeover"
            and any("security alert" in hit.label.lower() for hit in result.hits),
            70,
        ),
    ]
    for condition, floor in high_confidence_floors:
        if condition:
            result.base_score = max(result.base_score, floor)

    return result
