from __future__ import annotations

import os
from pathlib import Path

import pytest

TEST_DB = Path(__file__).resolve().parent / "_test_person_a.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["PERSON_B_SYNC_API_KEY"] = "test-b-key"
os.environ["PERSON_C_SYNC_API_KEY"] = "test-c-key"

from fastapi.testclient import TestClient  # noqa: E402

from api import app  # noqa: E402
from database import Base, engine  # noqa: E402


@pytest.fixture()
def client():
    if TEST_DB.exists():
        TEST_DB.unlink()
    Base.metadata.drop_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture()
def expense_payload():
    return {
        "amount": "250.50",
        "expense_date": "2026-10-05",
        "merchant": "Zomato lunch",
        "payment_method": "upi",
        "description": "Team lunch",
        "transaction_type": "expense",
        "currency": "INR",
    }
