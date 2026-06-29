"""End-to-end pipeline orchestration."""

from __future__ import annotations

from pipeline.deliver import push_to_instantly
from pipeline.export import save_leads
from pipeline.intent import score_companies
from pipeline.models import Lead
from pipeline.personalize import draft_email
from config import settings


def filter_warm_leads(leads: list[Lead]) -> list[Lead]:
    warm: list[Lead] = []
    for lead in leads:
        if not lead.intent:
            continue
        if not lead.intent.has_warm_intent:
            continue
        if lead.intent.icp_score < settings.min_icp_score:
            continue
        warm.append(lead)
    return warm[: settings.max_leads]


def run_pipeline(
    leads: list[Lead],
    *,
    output_path: str,
    dry_run: bool = True,
    send: bool = False,
) -> list[Lead]:
    if not leads:
        return []

    score_companies(leads, dry_run=dry_run)
    warm = filter_warm_leads(leads)

    for lead in warm:
        draft_email(lead, dry_run=dry_run)
        lead.status = "ready" if send and not dry_run else "drafted"

    if send and not dry_run:
        result = push_to_instantly(warm, dry_run=False)
        for lead in warm:
            lead.status = f"sent:{result.get('status', 'ok')}"

    save_leads(warm, output_path)
    return warm
