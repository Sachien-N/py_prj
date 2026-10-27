from __future__ import annotations

import os
from pathlib import Path

import pytest

TEST_DB = Path(__file__).resolve().parent / "_test_person_c.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["PERSON_A_SYNC_API_KEY"] = "test-c-key"
os.environ["MAX_READING_GAP_HOURS"] = "4"

from fastapi.testclient import TestClient  # noqa: E402

from api import app  # noqa: E402
from database import Base, SessionLocal, engine  # noqa: E402


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
def db(client):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
