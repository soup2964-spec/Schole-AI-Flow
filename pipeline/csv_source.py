"""Load leads from Clay CSV export (includes Claygent intent columns)."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from pipeline.models import CompanyIntent, HiringSignal, IntentSignal, Lead

COLUMN_ALIASES: dict[str, list[str]] = {
    "first_name": ["first_name", "First Name", "first name"],
    "last_name": ["last_name", "Last Name", "last name"],
    "title": ["title", "Job Title", "job_title", "Title"],
    "email": ["email", "Work Email", "work_email", "Email"],
    "company_name": ["company_name", "Company Name", "Company", "company"],
    "domain": ["domain", "Company Domain", "website", "Website"],
    "linkedin_url": ["linkedin_url", "LinkedIn URL", "linkedin", "Person Linkedin Url"],
    "headcount": ["headcount", "Employee Count", "# Employees", "estimated_num_employees"],
    "industry": ["industry", "Industry"],
    "warm_intent": ["warm_intent", "Warm Intent", "has_warm_intent"],
    "icp_score": ["icp_score", "ICP Score", "icp score"],
    "icp_tier": ["icp_tier", "ICP Tier"],
    "intent_evidence": ["intent_evidence", "Evidence", "signal_evidence"],
    "intent_ai_pilot": ["intent_ai_pilot", "AI Pilot Signal"],
    "intent_ai_hiring": ["intent_ai_hiring", "AI Hiring Signal"],
    "subject": ["subject", "Subject"],
    "body": ["body", "Body", "email_body"],
}


def _resolve_row(row: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    lower_map = {k.strip().lower(): v for k, v in row.items()}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            val = row.get(alias)
            if val:
                out[field] = val.strip()
                break
            val = lower_map.get(alias.lower())
            if val:
                out[field] = val.strip()
                break
    return out


def _truthy(value: str) -> bool:
    return value.strip().lower() in ("true", "yes", "1", "y")


def _parse_json_cell(raw: str) -> dict:
    raw = raw.strip()
    if not raw:
        return {}
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _intent_from_row(r: dict[str, str]) -> CompanyIntent | None:
    pilot_raw = r.get("intent_ai_pilot", "")
    hiring_raw = r.get("intent_ai_hiring", "")
    pilot_data = _parse_json_cell(pilot_raw)
    hiring_data = _parse_json_cell(hiring_raw)

    pilot_intent = _truthy(r.get("warm_intent", "")) or bool(pilot_data.get("intent"))
    hiring_intent = bool(hiring_data.get("hiring_ai_role"))

    if not pilot_raw and not hiring_raw and not r.get("warm_intent"):
        return None

    score_raw = r.get("icp_score", "")
    try:
        icp_score = int(float(score_raw)) if score_raw else (75 if (pilot_intent or hiring_intent) else 40)
    except ValueError:
        icp_score = 75 if (pilot_intent or hiring_intent) else 40

    evidence = r.get("intent_evidence") or pilot_data.get("evidence") or hiring_data.get("evidence") or "none"

    return CompanyIntent(
        domain=r.get("domain", ""),
        company_name=r.get("company_name", ""),
        ai_pilot=IntentSignal(
            intent=pilot_intent,
            signal_type=str(pilot_data.get("signal_type", "initiative" if pilot_intent else "none")),
            evidence=str(evidence),
        ),
        ai_hiring=HiringSignal(
            hiring_ai_role=hiring_intent,
            evidence=str(hiring_data.get("evidence", "none")),
        ),
        icp_score=icp_score,
        icp_tier=r.get("icp_tier") or ("A" if icp_score >= 70 else "C"),
        reason=str(pilot_data.get("reason") or hiring_data.get("reason") or evidence),
    )


def load_csv(path: str | Path) -> list[Lead]:
    path = Path(path)
    leads: list[Lead] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = _resolve_row(row)
            if not r.get("company_name") and not r.get("domain"):
                continue
            leads.append(
                Lead(
                    first_name=r.get("first_name", ""),
                    last_name=r.get("last_name", ""),
                    title=r.get("title", ""),
                    email=r.get("email", ""),
                    company_name=r.get("company_name", ""),
                    domain=r.get("domain", ""),
                    linkedin_url=r.get("linkedin_url", ""),
                    headcount=r.get("headcount", ""),
                    industry=r.get("industry", ""),
                    intent=_intent_from_row(r),
                    subject=r.get("subject", ""),
                    body=r.get("body", ""),
                )
            )
    return leads
