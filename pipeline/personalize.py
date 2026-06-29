"""Personalized cold email drafting."""

from __future__ import annotations

import json
import re

import httpx

from config import settings
from pipeline.models import Lead

EMAIL_PROMPT = """Write a cold email to {first_name}, {title} at {company_name}.

Warm signals:
- AI pilot/initiative: {ai_pilot}
- AI hiring: {ai_hiring}

About Scholé: AI upskilling platform that turns AI tools companies already bought
into measurable employee adoption. Role-specific lessons, HR dashboard for adoption.
Backed by EPFL/UC Berkeley; co-teaches Harvard AI intensives.

Rules: 70-90 words, plain text, open with THEIR signal, one CTA (20-min founder demo).
Return ONLY JSON: {{"subject":"...", "body":"..."}}
"""


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


def _mock_email(lead: Lead) -> tuple[str, str]:
    company = lead.company_name or lead.domain
    subject = f"AI adoption at {company}"
    body = (
        f"Hi {lead.first_name},\n\n"
        f"Saw {company} is investing in AI — most teams stall on adoption, not access. "
        f"Scholé helps L&D teams turn Copilot/ChatGPT rollouts into measurable skill gains "
        f"with role-specific lessons and an HR dashboard.\n\n"
        f"Worth a 20-min demo with a founder this week?\n\n"
        f"— KJ"
    )
    return subject, body


def draft_email(lead: Lead, *, dry_run: bool = False) -> Lead:
    if dry_run or not settings.openai_api_key:
        lead.subject, lead.body = _mock_email(lead)
        lead.status = "drafted"
        return lead

    intent = lead.intent
    prompt = EMAIL_PROMPT.format(
        first_name=lead.first_name,
        title=lead.title,
        company_name=lead.company_name,
        ai_pilot=intent.ai_pilot.model_dump() if intent else {},
        ai_hiring=intent.ai_hiring.model_dump() if intent else {},
    )

    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.openai_api_key}"},
            json={
                "model": settings.openai_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

    data = _parse_json(content)
    lead.subject = data.get("subject", "")
    lead.body = data.get("body", "")
    lead.status = "drafted"
    return lead
