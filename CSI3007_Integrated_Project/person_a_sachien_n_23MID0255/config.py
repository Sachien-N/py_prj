"""Configuration for Person A's expense manager.

All values can be overridden with environment variables or a local ``.env`` file.
The defaults are development-only values; see README.md before deploying.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=False)


def _sqlite_url(filename: str) -> str:
    return f"sqlite:///{(BASE_DIR / 'data' / filename).as_posix()}"


class Settings:
    app_name = "Smart Expense Categorization and Budget Manager"
    owner_name = "Sachien N"
    owner_registration = "23MID0255"
    project_dir = BASE_DIR

    database_url = os.getenv("DATABASE_URL", _sqlite_url("person_a.db"))
    api_host = os.getenv("API_HOST", "127.0.0.1")
    api_port = int(os.getenv("PORT", os.getenv("API_PORT", "8001")))
    api_base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8001")

    person_b_api_url = os.getenv("PERSON_B_API_URL", "http://127.0.0.1:8002")
    person_c_api_url = os.getenv("PERSON_C_API_URL", "http://127.0.0.1:8003")
    person_b_sync_api_key = os.getenv(
        "PERSON_B_SYNC_API_KEY", "dev-person-b-to-a-key"
    )
    person_c_sync_api_key = os.getenv(
        "PERSON_C_SYNC_API_KEY", "dev-person-c-to-a-key"
    )

    integration_timeout_seconds = float(
        os.getenv("INTEGRATION_TIMEOUT_SECONDS", "5")
    )
    integration_retries = int(os.getenv("INTEGRATION_RETRIES", "2"))
    cors_origins = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://127.0.0.1:8501,http://localhost:8501",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
