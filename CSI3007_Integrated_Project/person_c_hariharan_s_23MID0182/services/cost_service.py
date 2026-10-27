"""Cost estimates derived from socket consumption and configured tariffs."""

from __future__ import annotations

import calendar
from datetime import date

from sqlalchemy.orm import Session

from errors import AppError
from services.common import dec, money_str
from services.reading_service import aggregate_range
from services.tariff_service import calculate_estimate, select_tariff


def estimate_period_cost(db: Session, start_date: date, end_date: date) -> dict:
    aggregate = aggregate_range(db, start_date, end_date)
    if aggregate["interval_segments"] == 0:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "energy_kwh": aggregate["energy_kwh"],
            "coverage_pct": aggregate["coverage_pct"],
            "estimated_cost": None,
            "currency": "INR",
            "tariff": None,
            "is_estimate": True,
            "warnings": aggregate["warnings"],
            "message": "No usable readings; no cost was estimated.",
        }
    try:
        tariff = select_tariff(db, end_date, "domestic")
        estimate = calculate_estimate(
            db,
            units=dec(aggregate["energy_kwh"]),
            on_date=end_date,
            category=tariff.category,
            tariff_id=tariff.id,
        )
    except AppError as exc:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "energy_kwh": aggregate["energy_kwh"],
            "coverage_pct": aggregate["coverage_pct"],
            "estimated_cost": None,
            "currency": "INR",
            "tariff": None,
            "is_estimate": True,
            "warnings": [*aggregate["warnings"], exc.message],
            "message": "No active tariff configuration allowed a cost estimate.",
        }
    return {
        "start_date": start_date,
        "end_date": end_date,
        "energy_kwh": aggregate["energy_kwh"],
        "coverage_pct": aggregate["coverage_pct"],
        "estimated_cost": estimate["total_cost"],
        "energy_charge": estimate["energy_charge"],
        "component_total": estimate["component_total"],
        "currency": estimate["currency"],
        "tariff": estimate["tariff"],
        "is_estimate": True,
        "warnings": [*aggregate["warnings"], *estimate["warnings"]],
        "methodology": (
            "Progressive tariff slabs and configured components are applied to the "
            "socket-estimated units. This is not an official utility bill."
        ),
    }


def monthly_cost_series(db: Session, start_date: date, end_date: date) -> dict:
    if start_date > end_date:
        raise AppError("start_date cannot be after end_date", status_code=422)
    months = []
    cursor = date(start_date.year, start_date.month, 1)
    last = date(end_date.year, end_date.month, 1)
    while cursor <= last:
        month_start = max(cursor, start_date)
        month_end = min(
            date(cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1]),
            end_date,
        )
        estimate = estimate_period_cost(db, month_start, month_end)
        months.append(
            {
                "month": cursor.strftime("%Y-%m"),
                "period_start": month_start,
                "period_end": month_end,
                "energy_kwh": estimate["energy_kwh"],
                "estimated_cost": estimate["estimated_cost"],
                "coverage_pct": estimate["coverage_pct"],
                "tariff_name": estimate["tariff"]["name"] if estimate["tariff"] else None,
                "tariff_verified": (
                    estimate["tariff"]["is_verified"] if estimate["tariff"] else None
                ),
                "warnings": estimate["warnings"],
            }
        )
        cursor = (
            date(cursor.year + 1, 1, 1)
            if cursor.month == 12
            else date(cursor.year, cursor.month + 1, 1)
        )
    total = sum(
        (dec(month["estimated_cost"]) for month in months if month["estimated_cost"]),
        start=dec("0"),
    )
    return {
        "start_date": start_date,
        "end_date": end_date,
        "months": months,
        "total_estimated_cost": money_str(total),
        "currency": "INR",
        "is_estimate": True,
        "warnings": [
            "Every monthly value is an estimate from configured tariffs and partial socket coverage."
        ],
    }
