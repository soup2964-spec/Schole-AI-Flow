"""Warm-intent from Clay CSV export (Claygent columns). No external LLM."""

from __future__ import annotations

from pipeline.models import CompanyIntent, HiringSignal, IntentSignal, Lead


def score_companies(leads: list[Lead]) -> dict[str, CompanyIntent]:
    """Attach intent already parsed from Clay CSV; fill gaps with neutral defaults."""
    cache: dict[str, CompanyIntent] = {}
    for lead in leads:
        key = lead.domain or lead.company_name
        if lead.intent:
            cache[key] = lead.intent
            continue
        if key not in cache:
            cache[key] = CompanyIntent(
                domain=lead.domain,
                company_name=lead.company_name,
                ai_pilot=IntentSignal(intent=False, signal_type="none", evidence="none"),
                ai_hiring=HiringSignal(hiring_ai_role=False, evidence="none"),
                icp_score=0,
                icp_tier="C",
                reason="no intent columns in Clay export",
            )
        lead.intent = cache[key]
    return cache
