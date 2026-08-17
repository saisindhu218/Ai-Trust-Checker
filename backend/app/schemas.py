from pydantic import BaseModel
from typing import List, Optional


class ScanRequest(BaseModel):
    text: str


class ScanResponse(BaseModel):
    risk_score: int
    risk_level: str          # LOW / MEDIUM / HIGH
    confidence: str          # low / medium / high
    category: str
    red_flags: List[str]
    recommended_actions: List[str]
    summary: str
    ai_used: bool
    ai_error: Optional[str] = None
