"""Clay client — webhook push + optional Enterprise enrich API."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from config import settings


class ClayClient:
    BASE_URL = "https://api.clay.com/v1"

    def __init__(
        self,
        api_key: str | None = None,
        webhook_url: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.clay_api_key
        self.webhook_url = webhook_url or settings.clay_webhook_url

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def verify_api_key(self) -> dict[str, Any]:
        """Test Enterprise enrich endpoint. Works only on Enterprise plans."""
        if not self.api_key:
            raise ValueError("CLAY_API_KEY not set in .env")

        async with httpx.AsyncClient(timeout=30) as client:
            # Harmless lookup shape — may 404/422 if email unknown, but auth errors surface as 401
            response = await client.post(
                f"{self.BASE_URL}/people/enrich",
                headers=self._headers(),
                json={"email": "verify@example.com"},
            )
            return {
                "status_code": response.status_code,
                "ok": response.status_code in (200, 404, 422),
                "body": response.text[:500],
            }

    async def enrich_company(self, domain: str) -> dict[str, Any]:
        """Enterprise: lookup company by domain."""
        if not self.api_key:
            raise ValueError("CLAY_API_KEY not set in .env")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.BASE_URL}/companies/enrich",
                headers=self._headers(),
                json={"domain": domain},
            )
            response.raise_for_status()
            return response.json()

    async def push_to_table(self, row: dict[str, Any]) -> None:
        """Push one record into a Clay table via its webhook URL."""
        if not self.webhook_url:
            raise ValueError("CLAY_WEBHOOK_URL not set in .env")

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.webhook_url,
                json=row,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()

    async def push_batch(
        self,
        rows: list[dict[str, Any]],
        delay_seconds: float = 0.25,
    ) -> dict[str, int]:
        sent, failed = 0, 0
        for row in rows:
            try:
                await self.push_to_table(row)
                sent += 1
            except Exception:
                failed += 1
            await asyncio.sleep(delay_seconds)
        return {"sent": sent, "failed": failed}


def verify_sync() -> dict[str, Any]:
    return asyncio.run(ClayClient().verify_api_key())
