from __future__ import annotations

from pydantic import BaseModel, Field


class IntentSignal(BaseModel):
    intent: bool = False
    signal_type: str = "none"
    evidence: str = "none"


class HiringSignal(BaseModel):
    hiring_ai_role: bool = False
    evidence: str = "none"


class CompanyIntent(BaseModel):
    domain: str
    company_name: str
    ai_pilot: IntentSignal = Field(default_factory=IntentSignal)
    ai_hiring: HiringSignal = Field(default_factory=HiringSignal)
    icp_score: int = 0
    icp_tier: str = "C"
    reason: str = ""

    @property
    def has_warm_intent(self) -> bool:
        return self.ai_pilot.intent or self.ai_hiring.hiring_ai_role


class Lead(BaseModel):
    first_name: str
    last_name: str = ""
    title: str
    email: str = ""
    company_name: str
    domain: str
    linkedin_url: str = ""
    headcount: str = ""
    industry: str = ""
    intent: CompanyIntent | None = None
    subject: str = ""
    body: str = ""
    status: str = "pending"
