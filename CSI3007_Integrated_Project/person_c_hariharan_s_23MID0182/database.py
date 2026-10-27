"""SQLAlchemy setup, time helpers, and database initialisation."""

from __future__ import annotations

from collections.abc import Generator
from datetime import date, datetime, time, timezone
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_naive_utc(value: datetime) -> datetime:
    """Convert an aware datetime to naive UTC for consistent storage."""
    if value.tzinfo is None:
        raise ValueError("A timezone-aware datetime is required")
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def from_naive_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc)


def local_day_bounds(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    """Return naive-UTC bounds for inclusive local calendar dates."""
    start_local = datetime.combine(start_date, time.min, tzinfo=settings.timezone)
    end_local = datetime.combine(end_date, time.max, tzinfo=settings.timezone)
    return to_naive_utc(start_local), to_naive_utc(end_local)


def _engine_kwargs(url: str) -> dict:
    kwargs: dict = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


engine = create_engine(settings.database_url, **_engine_kwargs(settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


if settings.database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def init_db() -> None:
    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    import models  # noqa: F401
    from services.tariff_service import seed_demo_tariff

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_tariff(db)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
