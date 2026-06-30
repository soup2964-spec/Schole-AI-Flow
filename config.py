from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    clay_api_key: str = os.getenv("CLAY_API_KEY", "")
    clay_webhook_url: str = os.getenv("CLAY_WEBHOOK_URL", "")
    instantly_api_key: str = os.getenv("INSTANTLY_API_KEY", "")
    instantly_campaign_id: str = os.getenv("INSTANTLY_CAMPAIGN_ID", "")
    min_icp_score: int = int(os.getenv("MIN_ICP_SCORE", "70"))
    max_leads: int = int(os.getenv("MAX_LEADS", "50"))


settings = Settings()
