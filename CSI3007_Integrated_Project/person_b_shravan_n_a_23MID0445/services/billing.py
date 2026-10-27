"""Billing-cycle arithmetic and recurring-cost projections."""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from errors import AppError

CENT = Decimal("0.01")
CYCLE_MONTHS = {"monthly": 1, "quarterly": 3, "yearly": 12}


def q(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def annual_cost(
    amount: Decimal, billing_cycle: str, custom_interval_days: int | None = None
) -> Decimal:
    amount = Decimal(amount)
    if billing_cycle == "weekly":
        return q(amount * 52)
    if billing_cycle == "monthly":
        return q(amount * 12)
    if billing_cycle == "quarterly":
        return q(amount * 4)
    if billing_cycle == "yearly":
        return q(amount)
    if billing_cycle == "custom":
        if not custom_interval_days or custom_interval_days < 1:
            raise AppError("A custom cycle requires a positive interval in days", 422)
        return q(amount * Decimal(365) / Decimal(custom_interval_days))
    raise AppError("Unsupported billing cycle", 422)


def monthly_cost(
    amount: Decimal, billing_cycle: str, custom_interval_days: int | None = None
) -> Decimal:
    return q(annual_cost(amount, billing_cycle, custom_interval_days) / Decimal(12))


def add_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, month_index = divmod(index, 12)
    month = month_index + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def advance_once(
    value: date, billing_cycle: str, custom_interval_days: int | None = None
) -> date:
    if billing_cycle == "weekly":
        return value + timedelta(days=7)
    if billing_cycle in CYCLE_MONTHS:
        return add_months(value, CYCLE_MONTHS[billing_cycle])
    if billing_cycle == "custom":
        if not custom_interval_days or custom_interval_days < 1:
            raise AppError("A custom cycle requires a positive interval in days", 422)
        return value + timedelta(days=custom_interval_days)
    raise AppError("Unsupported billing cycle", 422)


def calculate_next_renewal(
    start_date: date,
    billing_cycle: str,
    custom_interval_days: int | None,
    after: date | None = None,
) -> date:
    """Return the first billing occurrence on/after ``after`` (default today)."""
    after = after or date.today()
    if billing_cycle == "custom":
        interval = custom_interval_days or 0
        if interval < 1:
            raise AppError("A custom cycle requires a positive interval in days", 422)
        if start_date >= after:
            return start_date
        days = (after - start_date).days
        steps = (days + interval - 1) // interval
        return start_date + timedelta(days=steps * interval)
    if billing_cycle == "weekly":
        if start_date >= after:
            return start_date
        days = (after - start_date).days
        weeks = (days + 6) // 7
        return start_date + timedelta(days=weeks * 7)
    if billing_cycle in CYCLE_MONTHS:
        step = CYCLE_MONTHS[billing_cycle]
        if start_date >= after:
            return start_date
        months = (after.year - start_date.year) * 12 + (after.month - start_date.month)
        steps = max(0, (months + step - 1) // step)
        candidate = add_months(start_date, steps * step)
        while candidate < after:
            steps += 1
            candidate = add_months(start_date, steps * step)
        return candidate
    raise AppError("Unsupported billing cycle", 422)


def next_renewal_after(
    current: date,
    billing_cycle: str,
    custom_interval_days: int | None,
) -> date:
    """Advance one full billing interval from the current renewal date."""
    return advance_once(current, billing_cycle, custom_interval_days)


def period_bounds(period: str) -> tuple[date, date]:
    try:
        year, month = map(int, period.split("-"))
        return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    except (ValueError, IndexError):
        raise AppError("period must use YYYY-MM format", 422)
