"""Configuration for Person B's subscription manager."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)


def _sqlite_url(filename: str) -> str:
    return f"sqlite:///{(BASE_DIR / 'data' / filename).as_posix()}"


class Settings:
    app_name = "Smart Subscription Manager"
    owner_name = "Shravan N A"
    owner_registration = "23MID0445"
    project_dir = BASE_DIR

    database_url = os.getenv("DATABASE_URL", _sqlite_url("person_b.db"))
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("PORT", os.getenv("API_PORT", "8002")))
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8002")

    person_a_api_url = os.getenv("PERSON_A_API_URL", "http://127.0.0.1:8001")
    person_a_sync_api_key = os.getenv(
        "PERSON_A_SYNC_API_KEY", "dev-person-b-to-a-key"
    )
    integration_timeout_seconds = float(
        os.getenv("INTEGRATION_TIMEOUT_SECONDS", "5")
    )
    integration_retries = int(os.getenv("INTEGRATION_RETRIES", "2"))
    upcoming_days = int(os.getenv("UPCOMING_DAYS", "30"))
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:8502,http://localhost:8502",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
