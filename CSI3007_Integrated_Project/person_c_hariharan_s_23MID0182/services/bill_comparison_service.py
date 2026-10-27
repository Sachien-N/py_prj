"""Compare socket-based estimates with actual electricity bills."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database import utcnow
from errors import AppError
from models import BillComparison, ElectricityBill, TariffConfig
from services.common import dec, money, money_str
from services.reading_service import aggregate_range
from services.tariff_service import calculate_estimate, get_tariff, select_tariff


def _serialize_comparison(db: Session, comparison: BillComparison) -> dict:
    bill = comparison.bill
    tariff = db.get(TariffConfig, comparison.tariff_id) if comparison.tariff_id else None
    try:
        analysis = json.loads(comparison.analysis_json or "{}")
    except json.JSONDecodeError:
        analysis = {}
    return {
        "comparison_id": comparison.id,
        "bill_id": comparison.bill_id,
        "bill_reference": bill.bill_reference if bill else None,
        "compared_at": comparison.compared_at,
        "billing_period_start": bill.billing_period_start if bill else None,
        "billing_period_end": bill.billing_period_end if bill else None,
        "estimated_units": f"{dec(comparison.estimated_units):.2f}",
        "actual_units": f"{dec(comparison.actual_units):.2f}",
        "unit_deviation": f"{dec(comparison.unit_deviation):.2f}",
        "estimated_cost": money_str(comparison.estimated_cost),
        "actual_cost": money_str(comparison.actual_cost),
        "cost_deviation": money_str(comparison.cost_deviation),
        "percentage_deviation": (
            f"{dec(comparison.percentage_deviation):.2f}"
            if comparison.percentage_deviation is not None
            else None
        ),
        "percentage_basis": "cost deviation ÷ estimated cost × 100; null when estimated cost is zero",
        "tolerance_percent": f"{dec(comparison.tolerance_percent):.2f}",
        "exceeds_tolerance": comparison.exceeds_tolerance,
        "data_coverage_pct": f"{dec(comparison.data_coverage_pct):.2f}",
        "is_estimate": True,
        "tariff": (
            {
                "id": tariff.id,
                "name": tariff.name,
                "effective_from": tariff.effective_from,
                "effective_to": tariff.effective_to,
                "source": tariff.source,
                "is_verified": tariff.is_verified,
            }
            if tariff
            else None
        ),
        "warnings": analysis.get("warnings", []),
        "six_month_analysis": analysis.get("six_month_analysis"),
        "disclaimer": (
            "The estimated charges depend on configured tariffs and partial socket coverage. "
            "This comparison does not establish that the utility bill is incorrect."
        ),
    }


def _calculate(db: Session, bill: ElectricityBill, tolerance: float, tariff_id: int | None) -> dict:
    if not 0 <= tolerance <= 100:
        raise AppError("tolerance_percent must be between 0 and 100", status_code=422)
    aggregate = aggregate_range(db, bill.billing_period_start, bill.billing_period_end)
    estimated_units = dec(aggregate["energy_kwh"])
    if aggregate["interval_segments"] == 0:
        raise AppError(
            "No usable socket readings exist for this billing period, so an estimate cannot be compared.",
            status_code=422,
            details={
                "coverage_pct": aggregate["coverage_pct"],
                "warnings": aggregate["warnings"],
            },
        )
    tariff = get_tariff(db, tariff_id) if tariff_id else select_tariff(
        db, bill.billing_period_end, "domestic"
    )
    estimate = calculate_estimate(
        db,
        units=estimated_units,
        on_date=bill.billing_period_end,
        category=tariff.category,
        tariff_id=tariff.id,
    )
    estimated_cost = dec(estimate["total_cost"])
    actual_units = dec(bill.billed_units)
    actual_cost = dec(bill.bill_amount)
    unit_deviation = actual_units - estimated_units
    cost_deviation = actual_cost - estimated_cost
    if estimated_cost > 0:
        percentage = (cost_deviation / estimated_cost * Decimal("100")).quantize(
            Decimal("0.01")
        )
    elif actual_cost == 0:
        percentage = Decimal("0.00")
    else:
        percentage = None
    exceeds = (
        abs(percentage) > dec(str(tolerance))
        if percentage is not None
        else abs(cost_deviation) > 0
    )
    period_days = (bill.billing_period_end - bill.billing_period_start).days + 1
    return {
        "bill": bill,
        "aggregate": aggregate,
        "estimate": estimate,
        "estimated_units": estimated_units,
        "estimated_cost": estimated_cost,
        "actual_units": actual_units,
        "actual_cost": actual_cost,
        "unit_deviation": unit_deviation,
        "cost_deviation": cost_deviation,
        "percentage": percentage,
        "exceeds": exceeds,
        "tolerance": tolerance,
        "period_days": period_days,
        "warnings": [
            *estimate["warnings"],
            *aggregate["warnings"],
            (
                "Cost deviation percentage is undefined because the estimated cost is zero."
                if percentage is None
                else "A positive cost deviation means the actual bill is higher than the socket-based estimate."
            ),
        ],
    }


def _upsert(db: Session, data: dict) -> BillComparison:
    bill = data["bill"]
    comparison = db.scalar(
        select(BillComparison).where(BillComparison.bill_id == bill.id)
    )
    if not comparison:
        comparison = BillComparison(bill_id=bill.id)
        db.add(comparison)
    comparison.compared_at = utcnow()
    comparison.estimated_units = data["estimated_units"]
    comparison.estimated_cost = money(data["estimated_cost"])
    comparison.actual_units = data["actual_units"]
    comparison.actual_cost = money(data["actual_cost"])
    comparison.unit_deviation = data["unit_deviation"]
    comparison.cost_deviation = money(data["cost_deviation"])
    comparison.percentage_deviation = (
        data["percentage"].quantize(Decimal("0.01"))
        if data["percentage"] is not None
        else None
    )
    comparison.tolerance_percent = dec(str(data["tolerance"]))
    comparison.exceeds_tolerance = data["exceeds"]
    comparison.data_coverage_pct = dec(str(data["aggregate"]["coverage_pct"]))
    comparison.tariff_id = data["estimate"]["tariff"]["id"]
    comparison.analysis_json = json.dumps(
        {
            "warnings": data["warnings"],
            "estimate": data["estimate"],
            "aggregate": {
                key: value
                for key, value in data["aggregate"].items()
                if key not in {"gaps"}
            },
            "gaps": data["aggregate"]["gaps"],
        },
        default=str,
    )
    db.commit()
    db.refresh(comparison)
    return comparison


def compare_bill(
    db: Session,
    bill_id: int,
    tolerance_percent: float | None = None,
    tariff_id: int | None = None,
) -> dict:
    bill = db.get(ElectricityBill, bill_id)
    if not bill:
        raise AppError("Electricity bill not found", status_code=404)
    tolerance = (
        tolerance_percent
        if tolerance_percent is not None
        else settings.discrepancy_tolerance_percent
    )
    data = _calculate(db, bill, tolerance, tariff_id)
    comparison = _upsert(db, data)
    result = _serialize_comparison(db, comparison)
    if data["exceeds"]:
        from services.historical_analysis_service import analyze_six_months

        analysis = analyze_six_months(db, bill.id, current_comparison=result)
        comparison.analysis_json = json.dumps(
            {
                "warnings": data["warnings"],
                "estimate": data["estimate"],
                "aggregate": {
                    key: value
                    for key, value in data["aggregate"].items()
                    if key not in {"gaps"}
                },
                "gaps": data["aggregate"]["gaps"],
                "six_month_analysis": analysis,
            },
            default=str,
        )
        db.commit()
        result["six_month_analysis"] = analysis
    return result


def get_comparison(db: Session, bill_id: int) -> dict:
    comparison = db.scalar(
        select(BillComparison).where(BillComparison.bill_id == bill_id)
    )
    if not comparison:
        return compare_bill(db, bill_id)
    return _serialize_comparison(db, comparison)
