"""Monthly reporting and trend aggregation."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from errors import AppError
from services.budget_service import budget_overview, month_bounds
from services.expense_service import expense_summary

MONTHS = 6


def _previous_months(month: str, count: int) -> list[str]:
    year, number = map(int, month.split("-"))
    result = []
    for offset in range(count):
        index = (year * 12 + number - 1) - offset
        result.append(f"{index // 12:04d}-{index % 12 + 1:02d}")
    return list(reversed(result))


def monthly_trend(db: Session, month: str, months: int = MONTHS) -> list[dict]:
    trend = []
    for item in _previous_months(month, months):
        start, end = month_bounds(item)
        summary = expense_summary(db, start_date=start, end_date=end)
        trend.append(
            {
                "month": item,
                "expenses": summary["total_expenses"],
                "refunds": summary["total_refunds"],
                "net": summary["net_spending"],
            }
        )
    return trend


def monthly_report(db: Session, month: str, months: int = MONTHS) -> dict:
    try:
        start, end = month_bounds(month)
    except (ValueError, IndexError):
        raise AppError("month must be a valid YYYY-MM value", status_code=422)
    summary = expense_summary(db, start_date=start, end_date=end)
    from services.expense_service import daily_trend

    return {
        "month": month,
        "period_start": start,
        "period_end": end,
        "summary": summary,
        "budgets": budget_overview(db, month),
        "daily_trend": daily_trend(db, start_date=start, end_date=end),
        "monthly_trend": monthly_trend(db, month, months),
    }
