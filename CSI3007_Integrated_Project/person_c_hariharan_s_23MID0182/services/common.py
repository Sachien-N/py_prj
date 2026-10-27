"""Date, decimal and coverage helpers."""

from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from config import settings
from database import from_naive_utc, to_naive_utc

KWH = Decimal("0.001")
MONEY = Decimal("0.01")


def dec(value) -> Decimal:
    return Decimal(str(value or "0"))


def kwh_str(value: Decimal | int | float | str | None) -> str:
    return f"{dec(value).quantize(KWH, rounding=ROUND_HALF_UP):.3f}"


def money(value: Decimal | int | float | str | None) -> Decimal:
    return dec(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def money_str(value: Decimal | int | float | str | None) -> str:
    return f"{money(value):.2f}"


def pct(value: Decimal | int | float | str | None) -> str:
    return f"{dec(value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


def month_bounds(period: str) -> tuple[date, date]:
    try:
        year, month = map(int, period.split("-"))
        if not 1 <= month <= 12:
            raise ValueError
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    except (ValueError, IndexError):
        raise ValueError("month must use YYYY-MM format")


def month_key(value: date) -> str:
    return value.strftime("%Y-%m")


def iter_months(start: date, end: date):
    current = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while current <= last:
        month_end = date(
            current.year, current.month, calendar.monthrange(current.year, current.month)[1]
        )
        yield max(current, start), min(month_end, end), current.strftime("%Y-%m")
        current = date(
            current.year + (1 if current.month == 12 else 0),
            1 if current.month == 12 else current.month + 1,
            1,
        )


def local_day_start_utc(day: date) -> datetime:
    return to_naive_utc(datetime.combine(day, time.min, tzinfo=settings.timezone))


def local_day_end_utc(day: date) -> datetime:
    return to_naive_utc(datetime.combine(day, time.max, tzinfo=settings.timezone))


def local_day_hours(day: date) -> float:
    start = datetime.combine(day, time.min, tzinfo=settings.timezone)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=settings.timezone)
    return (end - start).total_seconds() / 3600


def range_hours(start: date, end: date) -> float:
    start_dt = datetime.combine(start, time.min, tzinfo=settings.timezone)
    end_dt = datetime.combine(end + timedelta(days=1), time.min, tzinfo=settings.timezone)
    return (end_dt - start_dt).total_seconds() / 3600


def local_date_of_utc(value: datetime) -> date:
    return from_naive_utc(value).astimezone(settings.timezone).date()


def local_period_label(day: date) -> str:
    return day.strftime("%Y-%m")


def iso_z(value: datetime | None) -> str | None:
    if value is None:
        return None
    return from_naive_utc(value).isoformat().replace("+00:00", "Z")


def union_seconds(intervals: list[tuple[datetime, datetime]]) -> float:
    if not intervals:
        return 0.0
    ordered = sorted(intervals, key=lambda item: item[0])
    total = 0.0
    current_start, current_end = ordered[0]
    for start, end in ordered[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += (current_end - current_start).total_seconds()
            current_start, current_end = start, end
    total += (current_end - current_start).total_seconds()
    return max(total, 0.0)


def coverage_percent(intervals: list[tuple[datetime, datetime]], hours: float) -> float:
    if hours <= 0:
        return 0.0
    return min(100.0, round(union_seconds(intervals) / (hours * 3600) * 100, 2))
