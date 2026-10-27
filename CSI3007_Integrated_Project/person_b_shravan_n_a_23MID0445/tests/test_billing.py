from __future__ import annotations

from datetime import date
from decimal import Decimal

from services.billing import (
    annual_cost,
    calculate_next_renewal,
    monthly_cost,
    next_renewal_after,
)


def test_projection_for_each_supported_cycle():
    assert annual_cost(Decimal("100"), "weekly") == Decimal("5200.00")
    assert annual_cost(Decimal("100"), "monthly") == Decimal("1200.00")
    assert annual_cost(Decimal("300"), "quarterly") == Decimal("1200.00")
    assert annual_cost(Decimal("1200"), "yearly") == Decimal("1200.00")
    assert annual_cost(Decimal("100"), "custom", 30) == Decimal("1216.67")

    assert monthly_cost(Decimal("100"), "weekly") == Decimal("433.33")
    assert monthly_cost(Decimal("300"), "quarterly") == Decimal("100.00")
    assert monthly_cost(Decimal("1200"), "yearly") == Decimal("100.00")
    assert monthly_cost(Decimal("100"), "custom", 30) == Decimal("101.39")


def test_monthly_renewal_preserves_anchor_day_and_handles_month_end():
    assert calculate_next_renewal(
        date(2024, 1, 31), "monthly", None, after=date(2024, 2, 1)
    ) == date(2024, 2, 29)
    assert calculate_next_renewal(
        date(2024, 1, 31), "monthly", None, after=date(2024, 3, 1)
    ) == date(2024, 3, 31)
    assert calculate_next_renewal(
        date(2025, 2, 28), "yearly", None, after=date(2027, 1, 1)
    ) == date(2027, 2, 28)
    assert calculate_next_renewal(
        date(2026, 10, 1), "weekly", None, after=date(2026, 10, 16)
    ) == date(2026, 10, 22)
    assert calculate_next_renewal(
        date(2026, 1, 1), "custom", 45, after=date(2026, 2, 1)
    ) == date(2026, 2, 15)
    assert next_renewal_after(date(2026, 10, 31), "monthly", None) == date(
        2026, 11, 30
    )
