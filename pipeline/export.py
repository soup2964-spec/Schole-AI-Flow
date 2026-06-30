"""Export leads to CSV and Cursor-friendly draft queue."""

from __future__ import annotations

import csv
from pathlib import Path

from pipeline.models import Lead


def _signal_evidence(lead: Lead) -> str:
    if not lead.intent:
        return ""
    if lead.intent.ai_pilot.intent and lead.intent.ai_pilot.evidence not in ("none", ""):
        return lead.intent.ai_pilot.evidence
    if lead.intent.ai_hiring.hiring_ai_role and lead.intent.ai_hiring.evidence not in ("none", ""):
        return lead.intent.ai_hiring.evidence
    return lead.intent.reason or ""


def save_leads(leads: list[Lead], path: str | Path) -> None:
    """CSV for you to fill subject/body in Cursor, then run `send`."""
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
        "signal_evidence",
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
                    "signal_evidence": _signal_evidence(lead),
                    "subject": lead.subject,
                    "body": lead.body,
                    "status": lead.status,
                }
            )


def save_leads_for_cursor(leads: list[Lead], path: str | Path) -> None:
    """Markdown brief to paste into Cursor chat for email drafting."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Draft queue — paste this into Cursor",
        "",
        "Draft a cold email for **each lead** below. Rules:",
        "- 70-90 words, plain text",
        "- Open with their `signal_evidence`",
        "- Scholé = AI upskilling for L&D teams; measurable adoption; HR dashboard",
        "- CTA: 20-min founder demo",
        "",
        "Return a CSV with columns: email, subject, body",
        "",
        "---",
        "",
    ]

    for i, lead in enumerate(leads, 1):
        lines.extend(
            [
                f"## Lead {i}",
                f"- **Name:** {lead.first_name} {lead.last_name}".strip(),
                f"- **Title:** {lead.title}",
                f"- **Company:** {lead.company_name}",
                f"- **Email:** {lead.email}",
                f"- **Domain:** {lead.domain}",
                f"- **Signal:** {_signal_evidence(lead)}",
                "",
            ]
        )

    path.write_text("\n".join(lines), encoding="utf-8")
