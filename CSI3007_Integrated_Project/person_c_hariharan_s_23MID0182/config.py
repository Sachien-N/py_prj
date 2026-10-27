"""Configuration for Person C's electricity monitoring project."""

from __future__ import annotations

import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)


def _sqlite_url(filename: str) -> str:
    return f"sqlite:///{(BASE_DIR / 'data' / filename).as_posix()}"


class Settings:
    app_name = "Smart Home Electricity Monitoring and TNEB Bill Verification"
    owner_name = "HARIHARAN S"
    owner_registration = "23MID0182"
    project_dir = BASE_DIR

    database_url = os.getenv("DATABASE_URL", _sqlite_url("person_c.db"))
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("PORT", os.getenv("API_PORT", "8003")))
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8003")
    timezone_name = os.getenv("TIMEZONE", "Asia/Kolkata")
    timezone = ZoneInfo(timezone_name)

    person_a_api_url = os.getenv("PERSON_A_API_URL", "http://127.0.0.1:8001")
    person_a_sync_api_key = os.getenv(
        "PERSON_A_SYNC_API_KEY", "dev-person-c-to-a-key"
    )
    integration_timeout_seconds = float(
        os.getenv("INTEGRATION_TIMEOUT_SECONDS", "5")
    )
    integration_retries = int(os.getenv("INTEGRATION_RETRIES", "2"))

    discrepancy_tolerance_percent = float(
        os.getenv("DISCREPANCY_TOLERANCE_PERCENT", "10")
    )
    max_reading_gap_hours = float(os.getenv("MAX_READING_GAP_HOURS", "4"))
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:8503,http://localhost:8503",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
