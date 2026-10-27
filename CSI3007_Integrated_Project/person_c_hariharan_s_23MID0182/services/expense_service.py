"""Monthly electricity expense records for Person A."""

from __future__ import annotations

import calendar
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from errors import AppError
from models import ElectricityBill
from services.common import dec, money_str
from services.reading_service import aggregate_range
from services.tariff_service import calculate_estimate, select_tariff

MAX_MONTHS = 24


def _shift_month_start(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, month_index = divmod(index, 12)
    return date(year, month_index + 1, 1)


def default_expense_range() -> tuple[date, date]:
    today = date.today()
    start = _shift_month_start(today.replace(day=1), -5)
    return start, today


def _bill_for_month(db: Session, month_start: date, month_end: date):
    return db.scalar(
        select(ElectricityBill)
        .where(
            ElectricityBill.billing_period_start >= month_start,
            ElectricityBill.billing_period_start <= month_end,
        )
        .order_by(ElectricityBill.billing_period_start.desc(), ElectricityBill.id.desc())
        .limit(1)
    )


def monthly_expense_records(
    db: Session, start_date: date, end_date: date
) -> dict:
    if start_date > end_date:
        raise AppError("start_date cannot be after end_date", status_code=422)
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    if months > MAX_MONTHS:
        raise AppError(
            f"Electricity expense exports are limited to {MAX_MONTHS} months",
            status_code=422,
        )
    records = []
    warnings = []
    cursor = date(start_date.year, start_date.month, 1)
    last_month = date(end_date.year, end_date.month, 1)
    while cursor <= last_month:
        month_start = max(cursor, start_date)
        month_end = min(
            date(cursor.year, cursor.month, calendar.monthrange(cursor.year, cursor.month)[1]),
            end_date,
        )
        period = cursor.strftime("%Y-%m")
        bill = _bill_for_month(db, month_start, month_end)
        if bill:
            if dec(bill.bill_amount) <= 0:
                warnings.append(
                    f"{period}: recorded bill {bill.bill_reference} has a zero amount and "
                    "was not exported; no estimated amount was substituted."
                )
                cursor = _shift_month_start(cursor, 1)
                continue
            coverage = aggregate_range(
                db, bill.billing_period_start, bill.billing_period_end
            )
            description = (
                f"Actual electricity bill {bill.bill_reference} for "
                f"{bill.billing_period_start} to {bill.billing_period_end}. "
                "Imported as an actual bill amount, not a tariff estimate."
            )
            records.append(
                {
                    "source_app": "person_c",
                    "external_id": f"electricity:{period}",
                    "period": period,
                    "billing_date": bill.bill_date.isoformat(),
                    "expense_amount": money_str(bill.bill_amount),
                    "currency": "INR",
                    "units": f"{dec(bill.billed_units):.2f}",
                    "is_estimate": False,
                    "description": description,
                    "record_updated_at": bill.updated_at.isoformat(),
                    "data_coverage_pct": f"{coverage['coverage_pct']:.2f}",
                }
            )
        else:
            aggregate = aggregate_range(db, month_start, month_end)
            if aggregate["interval_segments"] == 0:
                warnings.append(
                    f"{period}: no socket readings and no recorded bill; no expense record was fabricated."
                )
                cursor = _shift_month_start(cursor, 1)
                continue
            try:
                tariff = select_tariff(db, month_end, "domestic")
                estimate = calculate_estimate(
                    db,
                    units=dec(aggregate["energy_kwh"]),
                    on_date=month_end,
                    category=tariff.category,
                    tariff_id=tariff.id,
                )
            except AppError as exc:
                warnings.append(f"{period}: estimate unavailable ({exc.message}).")
                cursor = _shift_month_start(cursor, 1)
                continue
            amount = dec(estimate["total_cost"])
            if amount <= 0:
                warnings.append(f"{period}: estimated amount was zero; no record was created.")
                cursor = _shift_month_start(cursor, 1)
                continue
            records.append(
                {
                    "source_app": "person_c",
                    "external_id": f"electricity:{period}",
                    "period": period,
                    "billing_date": month_end.isoformat(),
                    "expense_amount": money_str(amount),
                    "currency": "INR",
                    "units": aggregate["energy_kwh"],
                    "is_estimate": True,
                    "description": (
                        f"Estimated electricity cost for {period} using configured tariff "
                        f"“{estimate['tariff']['name']}”. This is not an actual bill. "
                        f"Reading coverage {aggregate['coverage_pct']:.2f}%."
                    ),
                    "record_updated_at": datetime.now(timezone.utc).isoformat(),
                    "data_coverage_pct": f"{aggregate['coverage_pct']:.2f}",
                }
            )
        cursor = _shift_month_start(cursor, 1)

    total = sum((dec(record["expense_amount"]) for record in records), Decimal("0"))
    warnings.append(
        "Electricity amounts are monthly summaries. Actual bills take precedence for the "
        "month in which their billing period starts; otherwise a configured-tariff estimate is used."
    )
    warnings.append(
        "Socket readings may not cover the whole household. Coverage is reported per record."
    )
    return {
        "start_date": start_date,
        "end_date": end_date,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "records": records,
        "summary": {
            "months": months,
            "records": len(records),
            "estimated_records": sum(1 for record in records if record["is_estimate"]),
            "actual_records": sum(1 for record in records if not record["is_estimate"]),
            "total_amount_inr": money_str(total),
            "currency": "INR",
        },
        "warnings": warnings,
    }


def build_person_a_payload(
    db: Session, start_date: date, end_date: date
) -> dict:
    result = monthly_expense_records(db, start_date, end_date)
    return {
        "source_app": "person_c",
        "generated_at": result["generated_at"],
        "summary": {
            **result["summary"],
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "note": (
                "Actual bills are used where recorded; otherwise configurable-tariff "
                "estimates are clearly marked. No missing month is invented."
            ),
        },
        "expense_records": result["records"],
    }
