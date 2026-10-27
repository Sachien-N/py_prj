"""Evidence-based six-month analysis for a bill comparison discrepancy.

Facts and possible explanations are deliberately separated. Missing readings and
missing bills are reported as missing; they are never fabricated.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timezone
from decimal import Decimal
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from errors import AppError
from models import BillComparison, ElectricityBill
from services.bill_comparison_service import _serialize_comparison
from services.common import dec, money_str
from services.reading_service import aggregate_range
from services.tariff_service import calculate_estimate, select_tariff

DISCLAIMER = (
    "This analysis compares socket-based estimates with recorded bills. It does not "
    "establish that TNEB/TANGEDCO issued an incorrect bill and makes no such claim."
)


def _month_index(value: date) -> int:
    return value.year * 12 + value.month - 1


def _month_start(index: int) -> date:
    year, month_index = divmod(index, 12)
    return date(year, month_index + 1, 1)


def _month_end(index: int) -> date:
    start = _month_start(index)
    return date(
        start.year, start.month, calendar.monthrange(start.year, start.month)[1]
    )


def _find_bill_for_month(db: Session, start: date, end: date):
    return db.scalar(
        select(ElectricityBill)
        .where(
            ElectricityBill.billing_period_start >= start,
            ElectricityBill.billing_period_start <= end,
        )
        .order_by(ElectricityBill.billing_period_start.desc())
        .limit(1)
    )


def analyze_six_months(
    db: Session, bill_id: int, current_comparison: dict | None = None
) -> dict:
    bill = db.get(ElectricityBill, bill_id)
    if not bill:
        raise AppError("Electricity bill not found", status_code=404)
    if current_comparison is None:
        comparison_row = db.scalar(
            select(BillComparison).where(BillComparison.bill_id == bill.id)
        )
        if comparison_row:
            current_comparison = _serialize_comparison(db, comparison_row)
        else:
            raise AppError(
                "Create a bill comparison before requesting six-month analysis",
                status_code=422,
            )

    current_start_index = _month_index(bill.billing_period_start)
    months = []
    readings_months = 0
    billed_months = 0
    all_gaps = []
    for offset in range(1, 7):
        index = current_start_index - offset
        start = _month_start(index)
        end = _month_end(index)
        aggregate = aggregate_range(db, start, end)
        estimated_units = (
            dec(aggregate["energy_kwh"]) if aggregate["interval_segments"] else None
        )
        estimate = None
        estimate_error = None
        if estimated_units is not None and estimated_units >= 0:
            try:
                tariff = select_tariff(db, end, "domestic")
                estimate = calculate_estimate(
                    db,
                    units=estimated_units,
                    on_date=end,
                    category=tariff.category,
                    tariff_id=tariff.id,
                )
            except AppError as exc:
                estimate_error = exc.message
        actual_bill = _find_bill_for_month(db, start, end)
        estimated_cost = dec(estimate["total_cost"]) if estimate else None
        actual_units = dec(actual_bill.billed_units) if actual_bill else None
        actual_cost = dec(actual_bill.bill_amount) if actual_bill else None
        percentage = None
        if (
            estimated_cost is not None
            and estimated_cost > 0
            and actual_cost is not None
        ):
            percentage = (actual_cost - estimated_cost) / estimated_cost * Decimal("100")
        if aggregate["interval_segments"]:
            readings_months += 1
        if actual_bill:
            billed_months += 1
        all_gaps.extend(aggregate["gaps"])
        months.append(
            {
                "month": start.strftime("%Y-%m"),
                "period_start": start,
                "period_end": end,
                "observed": bool(aggregate["interval_segments"]),
                "estimated_units": (
                    f"{estimated_units:.2f}" if estimated_units is not None else None
                ),
                "estimated_cost": money_str(estimated_cost) if estimated_cost is not None else None,
                "actual_bill_present": actual_bill is not None,
                "bill_reference": actual_bill.bill_reference if actual_bill else None,
                "actual_units": f"{actual_units:.2f}" if actual_units is not None else None,
                "actual_cost": money_str(actual_cost) if actual_cost is not None else None,
                "percentage_deviation": (
                    f"{percentage.quantize(Decimal('0.01')):.2f}"
                    if percentage is not None
                    else None
                ),
                "coverage_pct": aggregate["coverage_pct"],
                "reading_gaps": len(aggregate["gaps"]),
                "tariff_estimate_error": estimate_error,
            }
        )

    previous_observed = [month for month in months if month["observed"]]
    previous_with_bills = [month for month in months if month["actual_bill_present"]]
    current_actual_units = dec(current_comparison["actual_units"])
    current_estimated_units = dec(current_comparison["estimated_units"])
    current_actual_cost = dec(current_comparison["actual_cost"])
    current_estimated_cost = dec(current_comparison["estimated_cost"])
    current_period_days = (
        bill.billing_period_end - bill.billing_period_start
    ).days + 1
    current_daily_units = (
        current_actual_units / Decimal(current_period_days)
        if current_period_days > 0
        else Decimal("0")
    )
    historical_daily = []
    for month in previous_observed:
        actual = dec(month["actual_units"]) if month["actual_units"] else None
        estimate_units = dec(month["estimated_units"])
        days = (month["period_end"] - month["period_start"]).days + 1
        units = actual if actual is not None else estimate_units
        if units is not None and days > 0:
            historical_daily.append(units / Decimal(days))
    history_median = median(historical_daily) if historical_daily else None
    change_ratio = (
        current_daily_units / history_median
        if history_median and history_median > 0
        else None
    )
    significant_change = (
        change_ratio is not None and (change_ratio >= Decimal("1.30") or change_ratio <= Decimal("0.70"))
    )

    tolerance = dec(current_comparison["tolerance_percent"])
    prior_differences = []
    for month in months:
        if month["percentage_deviation"] is None:
            continue
        value = dec(month["percentage_deviation"])
        if abs(value) > tolerance:
            prior_differences.append(value)
    same_sign = 0
    if prior_differences:
        positive = sum(1 for value in prior_differences if value > 0)
        negative = sum(1 for value in prior_differences if value < 0)
        same_sign = max(positive, negative)
    recurring_estimation_difference = same_sign >= 2

    last_day = date(
        bill.billing_period_start.year,
        bill.billing_period_start.month,
        calendar.monthrange(
            bill.billing_period_start.year, bill.billing_period_start.month
        )[1],
    )
    period_mismatch = (
        bill.billing_period_start.day != 1 or bill.billing_period_end != last_day
    )
    missing_months = [
        month["month"] for month in months if not month["observed"]
    ]
    incomplete_months = [
        month["month"]
        for month in previous_observed
        if month["coverage_pct"] < 95
    ]
    insufficient = readings_months < 2 or billed_months < 1

    facts = [
        f"Current bill {bill.bill_reference} covers {current_period_days} days "
        f"({bill.billing_period_start} to {bill.billing_period_end}).",
        f"Actual billed units: {current_actual_units:.2f}; socket-estimated units: "
        f"{current_estimated_units:.2f}; unit deviation: "
        f"{current_actual_units - current_estimated_units:+.2f}.",
        f"Actual bill amount: ₹{current_actual_cost:.2f}; configured-tariff estimate: "
        f"₹{current_estimated_cost:.2f}; cost deviation: "
        f"₹{current_actual_cost - current_estimated_cost:+.2f}.",
        f"Current socket-reading coverage: {current_comparison['data_coverage_pct']}%.",
        f"Previous six months: {readings_months} month(s) with usable readings and "
        f"{billed_months} month(s) with a recorded bill.",
    ]
    if history_median is not None:
        facts.append(
            f"Current actual daily usage is {current_daily_units:.3f} units/day versus a "
            f"median historical daily usage of {history_median:.3f} units/day "
            f"(ratio {change_ratio:.2f})."
        )
    if significant_change:
        facts.append(
            "Observed usage is materially different from the historical median "
            "(outside the 0.70–1.30 ratio band)."
        )
    if missing_months:
        facts.append(
            "No usable socket reading interval was found for: "
            + ", ".join(missing_months)
            + "."
        )
    if incomplete_months:
        facts.append(
            "Reading coverage was below 95% in: " + ", ".join(incomplete_months) + "."
        )
    if all_gaps:
        facts.append(
            f"{len(all_gaps)} reading gap(s) longer than "
            f"{settings.max_reading_gap_hours:g} hours were excluded across the six months."
        )
    if period_mismatch:
        facts.append(
            "The current billing period does not align with a full calendar month, so "
            "monthly comparisons need period-length normalization."
        )
    if recurring_estimation_difference:
        facts.append(
            f"{same_sign} historical bill(s) showed a deviation beyond the "
            f"{tolerance:.2f}% tolerance in the same direction."
        )
    if insufficient:
        facts.append(
            "Insufficient historical data: at least two months with readings and one "
            "historical bill are needed for a stronger trend comparison."
        )

    explanations = [
        "Socket monitoring may not cover every circuit or appliance in the household.",
        "The configured tariff, fixed charges, duties, subsidies or effective dates may differ "
        "from those applied on the actual bill.",
        "Readings may be sparse or missing; intervals longer than the configured gap are excluded, "
        "which can under-estimate consumption.",
        "The billing period may not align with calendar months, and meter-reading dates can differ.",
        "Seasonal appliance use (for example air conditioning or water heating) can change consumption.",
        "Utility estimated billing or meter-reading timing can create period-to-period differences.",
        "A change in household occupancy or appliance usage may explain a genuine change in units.",
    ]
    warnings = list(current_comparison.get("warnings", []))
    warnings.append(DISCLAIMER)
    if insufficient:
        warnings.append(
            "The available history is insufficient to identify a recurring pattern; "
            "this report must not be treated as proof of a billing error."
        )
    if not previous_with_bills:
        warnings.append("No historical bills were available, so recurring bill differences cannot be assessed.")

    return {
        "bill_id": bill.id,
        "bill_reference": bill.bill_reference,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "analysis_window": {
            "months_requested": 6,
            "months_with_readings": readings_months,
            "months_with_bills": billed_months,
        },
        "current_period": {
            "period_start": bill.billing_period_start,
            "period_end": bill.billing_period_end,
            "period_days": current_period_days,
            "actual_units": current_comparison["actual_units"],
            "estimated_units": current_comparison["estimated_units"],
            "actual_cost": current_comparison["actual_cost"],
            "estimated_cost": current_comparison["estimated_cost"],
            "unit_deviation": current_comparison["unit_deviation"],
            "cost_deviation": current_comparison["cost_deviation"],
            "percentage_deviation": current_comparison["percentage_deviation"],
            "coverage_pct": current_comparison["data_coverage_pct"],
            "current_daily_units": f"{current_daily_units:.3f}",
        },
        "historical_months": months,
        "observed_facts": facts,
        "possible_explanations": explanations,
        "warnings": warnings,
        "insufficient_history": insufficient,
        "period_mismatch": period_mismatch,
        "significant_change": significant_change,
        "historical_median_daily_units": (
            f"{history_median:.3f}" if history_median is not None else None
        ),
        "usage_change_ratio": (
            f"{change_ratio:.2f}" if change_ratio is not None else None
        ),
        "recurring_estimation_difference": recurring_estimation_difference,
        "missing_reading_months": missing_months,
        "incomplete_coverage_months": incomplete_months,
        "disclaimer": DISCLAIMER,
    }
