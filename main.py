#!/usr/bin/env python3
"""Scholé AI Flow — US lead-gen pipeline for L&D / CHRO decision-makers."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from pipeline.apollo_source import search_people
from pipeline.clay_client import ClayClient, verify_sync
from pipeline.csv_source import load_csv
from pipeline.export import save_leads
from pipeline.runner import run_pipeline


def cmd_verify_clay(_: argparse.Namespace) -> None:
    result = verify_sync()
    print(f"Clay API check: HTTP {result['status_code']}")
    if result["ok"]:
        print("Key accepted (Enterprise enrich endpoint reachable).")
    else:
        print("Key rejected or plan lacks Enterprise API.")
        print(result["body"])


def cmd_source_apollo(args: argparse.Namespace) -> None:
    leads = search_people(per_page=args.limit, page=1)
    out = Path(args.output)
    save_leads(leads, out)
    print(f"Saved {len(leads)} leads to {out}")


def cmd_push_clay(args: argparse.Namespace) -> None:
    leads = load_csv(args.input)
    client = ClayClient()
    rows = [
        {
            "first_name": l.first_name,
            "last_name": l.last_name,
            "title": l.title,
            "email": l.email,
            "company_name": l.company_name,
            "domain": l.domain,
            "linkedin_url": l.linkedin_url,
        }
        for l in leads
    ]
    result = asyncio.run(client.push_batch(rows))
    print(f"Pushed to Clay webhook: {result}")


def cmd_run(args: argparse.Namespace) -> None:
    if args.input:
        leads = load_csv(args.input)
    else:
        leads = search_people(per_page=args.limit)

    warm = run_pipeline(
        leads,
        output_path=args.output,
        dry_run=not args.live,
        send=args.send,
    )
    print(f"Pipeline done: {len(warm)} warm leads → {args.output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scholé AI Flow")
    sub = parser.add_subparsers(dest="command", required=True)

    p_verify = sub.add_parser("verify-clay", help="Test CLAY_API_KEY")
    p_verify.set_defaults(func=cmd_verify_clay)

    p_apollo = sub.add_parser("source-apollo", help="Pull US L&D/CHRO leads via Apollo")
    p_apollo.add_argument("--output", default="data/leads_raw.csv")
    p_apollo.add_argument("--limit", type=int, default=25)
    p_apollo.set_defaults(func=cmd_source_apollo)

    p_clay = sub.add_parser("push-clay", help="Push CSV rows into Clay webhook table")
    p_clay.add_argument("--input", required=True)
    p_clay.set_defaults(func=cmd_push_clay)

    p_run = sub.add_parser("run", help="Full pipeline: intent → personalize → export/send")
    p_run.add_argument("--input", help="CSV from Clay/Apollo (optional)")
    p_run.add_argument("--output", default="data/leads_qualified.csv")
    p_run.add_argument("--limit", type=int, default=25)
    p_run.add_argument("--live", action="store_true", help="Use real LLM (not mock)")
    p_run.add_argument("--send", action="store_true", help="Push to Instantly (requires --live)")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
