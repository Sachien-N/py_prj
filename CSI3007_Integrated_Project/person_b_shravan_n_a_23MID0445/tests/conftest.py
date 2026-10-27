from __future__ import annotations

import os
from pathlib import Path

import pytest

TEST_DB = Path(__file__).resolve().parent / "_test_person_b.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB.as_posix()}"
os.environ["PERSON_A_SYNC_API_KEY"] = "test-a-key"

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
