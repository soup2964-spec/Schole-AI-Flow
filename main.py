#!/usr/bin/env python3
"""
Scholé AI Flow

  1. Clay     — source + enrich + warm-intent (Clay UI, export CSV)
  2. Cursor   — draft emails (paste data/cursor_draft_queue.md into chat)
  3. Instantly — send (python main.py send)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from pipeline.clay_client import ClayClient, verify_sync
from pipeline.csv_source import load_csv
from pipeline.runner import filter_from_clay
from pipeline.send import send_to_instantly


def cmd_verify_clay(_: argparse.Namespace) -> None:
    result = verify_sync()
    print(f"Clay API check: HTTP {result['status_code']}")
    if result["ok"]:
        print("Key accepted (Enterprise enrich endpoint reachable).")
    else:
        print("Key rejected or plan lacks Enterprise API.")
        print(result["body"])


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


def cmd_filter(args: argparse.Namespace) -> None:
    leads = load_csv(args.input)
    warm = filter_from_clay(
        leads,
        csv_output=args.output,
        cursor_output=args.cursor,
    )
    print(f"Filtered {len(warm)} warm leads")
    print(f"  CSV (fill subject/body after Cursor): {args.output}")
    print(f"  Cursor brief: {args.cursor}")
    if not warm and leads:
        print(
            "Tip: Clay export needs warm_intent / intent_ai_pilot / icp_score columns.",
            file=sys.stderr,
        )


def cmd_send(args: argparse.Namespace) -> None:
    leads = load_csv(args.input)
    result = send_to_instantly(leads, output_path=args.output)
    print(f"Sent {len(leads)} leads to Instantly")
    print(f"  Result: {result}")
    print(f"  Log: {args.output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scholé AI Flow: Clay -> Cursor -> Instantly")
    sub = parser.add_subparsers(dest="command", required=True)

    p_verify = sub.add_parser("verify-clay", help="Test CLAY_API_KEY")
    p_verify.set_defaults(func=cmd_verify_clay)

    p_clay = sub.add_parser("push-clay", help="Push rows into Clay webhook table")
    p_clay.add_argument("--input", required=True)
    p_clay.set_defaults(func=cmd_push_clay)

    p_filter = sub.add_parser("filter", help="Clay export -> warm leads + Cursor draft queue")
    p_filter.add_argument("--input", required=True, help="Clay CSV export")
    p_filter.add_argument("--output", default="data/to_draft.csv")
    p_filter.add_argument("--cursor", default="data/cursor_draft_queue.md")
    p_filter.set_defaults(func=cmd_filter)

    p_send = sub.add_parser("send", help="Drafted CSV -> Instantly")
    p_send.add_argument("--input", required=True, help="CSV with email, subject, body filled")
    p_send.add_argument("--output", default="data/sent_log.csv")
    p_send.set_defaults(func=cmd_send)

    args = parser.parse_args()
    try:
        args.func(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
