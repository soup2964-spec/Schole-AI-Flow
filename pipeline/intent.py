"""Warm-intent detection + ICP scoring via LLM."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from config import settings
from pipeline.models import CompanyIntent, HiringSignal, IntentSignal, Lead


INTENT_PROMPT = """You are researching whether a US company is a warm prospect for Scholé,
an AI upskilling platform sold to L&D / People teams.

Company: {company_name}
Domain: {domain}
Industry: {industry}
Headcount: {headcount}

Based on public signals (AI pilot programs, Copilot/ChatGPT Enterprise rollouts,
AI task forces, AI enablement hiring), assess warm intent.

Return ONLY valid JSON:
{{
  "ai_pilot": {{"intent": true/false, "signal_type": "pilot|rollout|task force|initiative|none", "evidence": "..."}},
  "ai_hiring": {{"hiring_ai_role": true/false, "evidence": "..."}},
  "icp_score": 0-100,
  "icp_tier": "A|B|C",
  "reason": "one sentence"
}}
"""


def _parse_json(text: str) -> dict[str, Any]:
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _mock_intent(lead: Lead) -> CompanyIntent:
    """Heuristic intent for dry-run without OpenAI."""
    domain = lead.domain.lower()
    name = lead.company_name.lower()
    warm_keywords = ("ai", "tech", "software", "digital", "data")
    warm = any(k in domain or k in name for k in warm_keywords)
    return CompanyIntent(
        domain=lead.domain,
        company_name=lead.company_name,
        ai_pilot=IntentSignal(
            intent=warm,
            signal_type="initiative" if warm else "none",
            evidence="dry-run heuristic" if warm else "none",
        ),
        ai_hiring=HiringSignal(hiring_ai_role=False, evidence="none"),
        icp_score=75 if warm else 40,
        icp_tier="A" if warm else "C",
        reason="dry-run mock scoring",
    )


def detect_intent(lead: Lead, *, dry_run: bool = False) -> CompanyIntent:
    if dry_run or not settings.openai_api_key:
        return _mock_intent(lead)

    prompt = INTENT_PROMPT.format(
        company_name=lead.company_name,
        domain=lead.domain,
        industry=lead.industry or "unknown",
        headcount=lead.headcount or "unknown",
    )

    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

    data = _parse_json(content)
    ai_pilot = data.get("ai_pilot", {})
    ai_hiring = data.get("ai_hiring", {})
    return CompanyIntent(
        domain=lead.domain,
        company_name=lead.company_name,
        ai_pilot=IntentSignal(
            intent=bool(ai_pilot.get("intent")),
            signal_type=str(ai_pilot.get("signal_type", "none")),
            evidence=str(ai_pilot.get("evidence", "none")),
        ),
        ai_hiring=HiringSignal(
            hiring_ai_role=bool(ai_hiring.get("hiring_ai_role")),
            evidence=str(ai_hiring.get("evidence", "none")),
        ),
        icp_score=int(data.get("icp_score", 0)),
        icp_tier=str(data.get("icp_tier", "C")),
        reason=str(data.get("reason", "")),
    )


def score_companies(leads: list[Lead], *, dry_run: bool = False) -> dict[str, CompanyIntent]:
    """Score each unique company once, attach intent to all people at that company."""
    cache: dict[str, CompanyIntent] = {}
    for lead in leads:
        key = lead.domain or lead.company_name
        if key not in cache:
            cache[key] = detect_intent(lead, dry_run=dry_run)
        lead.intent = cache[key]
    return cache
