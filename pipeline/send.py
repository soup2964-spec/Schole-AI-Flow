"""Send drafted emails to Instantly."""

from __future__ import annotations

from pipeline.deliver import push_to_instantly
from pipeline.export import save_leads
from pipeline.models import Lead


def send_to_instantly(leads: list[Lead], *, output_path: str) -> dict:
    missing = [l for l in leads if not l.email or not l.subject or not l.body]
    if missing:
        names = ", ".join(l.email or l.company_name for l in missing[:5])
        raise ValueError(
            f"{len(missing)} lead(s) missing email, subject, or body (e.g. {names}). "
            "Draft in Cursor first, then save CSV with subject/body filled."
        )

    result = push_to_instantly(leads, dry_run=False)
    for lead in leads:
        lead.status = f"sent:{result.get('status', 'ok')}"
    save_leads(leads, output_path)
    return result
