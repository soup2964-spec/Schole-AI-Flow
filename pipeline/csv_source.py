"""Load leads from CSV (Clay export or Apollo export)."""

from __future__ import annotations

import csv
from pathlib import Path

from pipeline.models import Lead

# Map common Clay / Apollo column names → our schema
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
                )
            )
    return leads
