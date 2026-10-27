"""Monetary helpers."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

CENT = Decimal("0.01")


def money(value: Decimal | int | float | str | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def money_str(value: Decimal | int | float | str | None) -> str:
    return f"{money(value):.2f}"
