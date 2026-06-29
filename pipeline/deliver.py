"""Push qualified leads to Instantly."""

from __future__ import annotations

from typing import Any

import httpx

from config import settings
from pipeline.models import Lead

INSTANTLY_ADD_URL = "https://api.instantly.ai/api/v2/leads/add"


def push_to_instantly(leads: list[Lead], *, dry_run: bool = True) -> dict[str, Any]:
    if dry_run:
        return {"dry_run": True, "would_send": len(leads)}

    if not settings.instantly_api_key or not settings.instantly_campaign_id:
        raise ValueError("INSTANTLY_API_KEY and INSTANTLY_CAMPAIGN_ID required")

    payload_leads = []
    for lead in leads:
        if not lead.email:
            continue
        payload_leads.append(
            {
                "email": lead.email,
                "first_name": lead.first_name,
                "last_name": lead.last_name,
                "company_name": lead.company_name,
                "custom_variables": {
                    "subject": lead.subject,
                    "body": lead.body,
                    "title": lead.title,
                    "domain": lead.domain,
                },
            }
        )

    if not payload_leads:
        return {"sent": 0, "message": "no leads with email"}

    with httpx.Client(timeout=60) as client:
        response = client.post(
            INSTANTLY_ADD_URL,
            headers={
                "Authorization": f"Bearer {settings.instantly_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "campaign_id": settings.instantly_campaign_id,
                "leads": payload_leads,
                "verify_leads_on_import": True,
            },
        )
        response.raise_for_status()
        return response.json()
