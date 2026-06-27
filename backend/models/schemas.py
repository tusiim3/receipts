from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    code: str


class UserProfile(BaseModel):
    uid: str
    email: str
    displayName: Optional[str] = None
    createdAt: Optional[str] = None


class Subscription(BaseModel):
    service_name: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    frequency: Literal["monthly", "annual", "weekly", "one-time", "unknown"] = "unknown"
    last_charge_date: Optional[str] = None
    trial_end_date: Optional[str] = None
    is_trial: bool = False
    source_email_subject: Optional[str] = None
    category: Optional[str] = None


class TosFlag(BaseModel):
    flag_title: str
    severity: Literal["high", "medium", "low"]
    explanation: str
    exact_quote: Optional[str] = None
    category: str


class TosAnalysisRequest(BaseModel):
    url: str


class TosAnalysisResult(BaseModel):
    flags: list[TosFlag]
    risk_summary: str
    source: str
    analyzed_at: str


class Alternative(BaseModel):
    name: str
    estimated_monthly_cost: str
    key_difference: str
    source_url: str


class SentimentResult(BaseModel):
    sentiment: Literal["positive", "mixed", "negative"]
    summary: str
    sources: list[str]


class AlternativesRequest(BaseModel):
    service_name: str
    current_amount: float
    currency: str
    frequency: str = "monthly"


class SentimentRequest(BaseModel):
    service_name: str


class WastefulFlag(BaseModel):
    type: str
    message: str
    services: list[str] = Field(default_factory=list)


class IntelligenceSummary(BaseModel):
    subscriptions: list[Subscription]
    total_monthly_spend: float
    currency: str = "USD"
    grouped_by_category: dict[str, list[Subscription]]
    wasteful_flags: list[WastefulFlag]
    tos_analyses: list[dict[str, Any]]
