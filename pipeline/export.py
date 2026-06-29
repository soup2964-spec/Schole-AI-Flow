"""Export leads to CSV for Clay import or review."""

from __future__ import annotations

import csv
from pathlib import Path

from pipeline.models import Lead


def save_leads(leads: list[Lead], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "first_name",
        "last_name",
        "title",
        "email",
        "company_name",
        "domain",
        "linkedin_url",
        "headcount",
        "industry",
        "icp_score",
        "warm_intent",
        "subject",
        "body",
        "status",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for lead in leads:
            intent = lead.intent
            writer.writerow(
                {
                    "first_name": lead.first_name,
                    "last_name": lead.last_name,
                    "title": lead.title,
                    "email": lead.email,
                    "company_name": lead.company_name,
                    "domain": lead.domain,
                    "linkedin_url": lead.linkedin_url,
                    "headcount": lead.headcount,
                    "industry": lead.industry,
                    "icp_score": intent.icp_score if intent else "",
                    "warm_intent": intent.has_warm_intent if intent else "",
                    "subject": lead.subject,
                    "body": lead.body,
                    "status": lead.status,
                }
            )
