from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ScanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10000)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("text must not be blank")
        return value


class AIResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    summary: str = Field(default="", max_length=1000)
    recommended_actions: List[str] = Field(default_factory=list, max_length=5)
    confidence: Literal["low", "medium", "high"] = "medium"
    category: str = Field(default="Unknown", max_length=100)
    score_adjustment: int = Field(default=0, ge=-20, le=20)


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
