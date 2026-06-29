"""Apollo.io people search — programmatic alternative to Clay Find People."""

from __future__ import annotations

from typing import Any

import httpx

from config import settings
from pipeline.models import Lead

# US enterprise L&D / People / AI decision-makers for Scholé ICP
DEFAULT_TITLES = [
    "VP Learning and Development",
    "Head of Learning and Development",
    "Director Learning and Development",
    "Chief Learning Officer",
    "CHRO",
    "Chief People Officer",
    "VP People Development",
    "Head of People Development",
    "Chief AI Officer",
    "Head of AI Enablement",
    "Director AI Transformation",
]

DEFAULT_EMPLOYEE_RANGES = ["501,1000", "1001,5000", "5001,10000", "10001,20000"]


def search_people(
    *,
    titles: list[str] | None = None,
    locations: list[str] | None = None,
    employee_ranges: list[str] | None = None,
    per_page: int = 25,
    page: int = 1,
) -> list[Lead]:
    if not settings.apollo_api_key:
        raise ValueError("APOLLO_API_KEY not set in .env (or use Clay Find People + export CSV)")

    titles = titles or DEFAULT_TITLES
    locations = locations or ["United States"]
    employee_ranges = employee_ranges or DEFAULT_EMPLOYEE_RANGES

    payload: dict[str, Any] = {
        "api_key": settings.apollo_api_key,
        "person_titles": titles,
        "person_locations": locations,
        "organization_num_employees_ranges": employee_ranges,
        "page": page,
        "per_page": per_page,
    }

    with httpx.Client(timeout=60) as client:
        response = client.post(
            "https://api.apollo.io/api/v1/mixed_people/search",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    leads: list[Lead] = []
    for person in data.get("people", []):
        org = person.get("organization") or {}
        domain = org.get("primary_domain") or org.get("website_url") or ""
        if domain.startswith("http"):
            domain = domain.replace("https://", "").replace("http://", "").split("/")[0]

        email = person.get("email") or ""
        leads.append(
            Lead(
                first_name=person.get("first_name") or "",
                last_name=person.get("last_name") or "",
                title=person.get("title") or "",
                email=email,
                company_name=org.get("name") or person.get("organization_name") or "",
                domain=domain,
                linkedin_url=person.get("linkedin_url") or "",
                headcount=str(org.get("estimated_num_employees") or ""),
                industry=org.get("industry") or "",
            )
        )
    return leads
