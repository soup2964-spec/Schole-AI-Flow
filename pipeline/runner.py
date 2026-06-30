"""Filter warm leads from Clay export — no auto email drafting."""

from __future__ import annotations

from config import settings
from pipeline.export import save_leads, save_leads_for_cursor
from pipeline.intent import score_companies
from pipeline.models import Lead


def filter_warm_leads(leads: list[Lead]) -> list[Lead]:
    warm: list[Lead] = []
    for lead in leads:
        if not lead.intent:
            continue
        if not lead.intent.has_warm_intent:
            continue
        if lead.intent.icp_score < settings.min_icp_score:
            continue
        lead.status = "needs_draft"
        warm.append(lead)
    return warm[: settings.max_leads]


def filter_from_clay(
    leads: list[Lead],
    *,
    csv_output: str,
    cursor_output: str,
) -> list[Lead]:
    if not leads:
        return []

    score_companies(leads)
    warm = filter_warm_leads(leads)
    save_leads(warm, csv_output)
    save_leads_for_cursor(warm, cursor_output)
    return warm
