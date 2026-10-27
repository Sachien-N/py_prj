"""Manual electricity bill capture, listing and validated CSV import."""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from errors import AppError
from models import BillComparison, ElectricityBill
from schemas import BillCreate
from services.common import money, money_str

MAX_ROWS = 2000
REQUIRED_HEADERS = {
    "bill_reference",
    "billing_period_start",
    "billing_period_end",
    "billed_units",
    "bill_amount",
    "bill_date",
}
KNOWN_HEADERS = REQUIRED_HEADERS | {
    "fixed_charges",
    "other_charges",
    "source",
    "notes",
}


def serialize_bill(bill: ElectricityBill) -> dict:
    return {
        "id": bill.id,
        "bill_reference": bill.bill_reference,
        "billing_period_start": bill.billing_period_start,
        "billing_period_end": bill.billing_period_end,
        "billed_units": f"{Decimal(bill.billed_units):.2f}",
        "bill_amount": money_str(bill.bill_amount),
        "fixed_charges": money_str(bill.fixed_charges),
        "other_charges": money_str(bill.other_charges),
        "bill_date": bill.bill_date,
        "source": bill.source,
        "notes": bill.notes,
        "created_at": bill.created_at,
        "updated_at": bill.updated_at,
        "has_comparison": bill.comparison is not None,
    }


def get_bill(db: Session, bill_id: int) -> ElectricityBill:
    bill = db.get(ElectricityBill, bill_id)
    if not bill:
        raise AppError("Electricity bill not found", status_code=404)
    return bill


def create_bill(db: Session, payload: BillCreate) -> ElectricityBill:
    if db.scalar(
        select(ElectricityBill).where(
            ElectricityBill.bill_reference == payload.bill_reference
        )
    ):
        raise AppError("A bill with that reference already exists", status_code=409)
    bill = ElectricityBill(
        bill_reference=payload.bill_reference,
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        billed_units=Decimal(payload.billed_units),
        bill_amount=money(payload.bill_amount),
        fixed_charges=money(payload.fixed_charges),
        other_charges=money(payload.other_charges),
        bill_date=payload.bill_date,
        source=payload.source,
        notes=payload.notes,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


def list_bills(db: Session, start_date: date | None = None, end_date: date | None = None):
    stmt = select(ElectricityBill).order_by(
        ElectricityBill.billing_period_start.desc(), ElectricityBill.id.desc()
    )
    if start_date:
        stmt = stmt.where(ElectricityBill.billing_period_end >= start_date)
    if end_date:
        stmt = stmt.where(ElectricityBill.billing_period_start <= end_date)
    return list(db.scalars(stmt).all())


def delete_bill(db: Session, bill_id: int) -> None:
    bill = get_bill(db, bill_id)
    db.delete(bill)
    db.commit()


def import_bills_csv(db: Session, raw: bytes) -> dict:
    if len(raw) > 2 * 1024 * 1024:
        raise AppError("CSV file is larger than the 2 MB limit", status_code=413)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise AppError("CSV must be UTF-8 encoded", status_code=422)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise AppError("CSV has no header row", status_code=422)
    headers = {name.strip().lower() for name in reader.fieldnames if name}
    missing = REQUIRED_HEADERS - headers
    if missing:
        raise AppError(
            "CSV is missing required columns: " + ", ".join(sorted(missing)),
            status_code=422,
        )
    unknown = headers - KNOWN_HEADERS
    if unknown:
        raise AppError(
            "CSV contains unsupported columns: " + ", ".join(sorted(unknown)),
            status_code=422,
        )
    errors = []
    prepared = []
    references = set()
    for line_number, source_row in enumerate(reader, start=2):
        if line_number - 1 > MAX_ROWS:
            raise AppError(f"CSV exceeds the {MAX_ROWS} row limit", status_code=422)
        row = {
            (key or "").strip().lower(): (value or "").strip()
            for key, value in source_row.items()
        }
        if not any(row.values()):
            continue
        try:
            payload = BillCreate(
                bill_reference=row.get("bill_reference", ""),
                billing_period_start=date.fromisoformat(row.get("billing_period_start", "")),
                billing_period_end=date.fromisoformat(row.get("billing_period_end", "")),
                billed_units=Decimal(row.get("billed_units", "")),
                bill_amount=Decimal(row.get("bill_amount", "")),
                fixed_charges=Decimal(row.get("fixed_charges") or "0"),
                other_charges=Decimal(row.get("other_charges") or "0"),
                bill_date=date.fromisoformat(row.get("bill_date", "")),
                source=row.get("source") or "csv",
                notes=row.get("notes", ""),
            )
            if payload.bill_reference in references:
                raise ValueError("duplicate bill_reference within CSV")
            references.add(payload.bill_reference)
            if db.scalar(
                select(ElectricityBill).where(
                    ElectricityBill.bill_reference == payload.bill_reference
                )
            ):
                raise ValueError("bill_reference already exists in the database")
            prepared.append(
                ElectricityBill(
                    bill_reference=payload.bill_reference,
                    billing_period_start=payload.billing_period_start,
                    billing_period_end=payload.billing_period_end,
                    billed_units=payload.billed_units,
                    bill_amount=money(payload.bill_amount),
                    fixed_charges=money(payload.fixed_charges),
                    other_charges=money(payload.other_charges),
                    bill_date=payload.bill_date,
                    source=payload.source,
                    notes=payload.notes,
                )
            )
        except (ValidationError, ValueError, InvalidOperation) as exc:
            message = str(exc)
            if isinstance(exc, ValidationError):
                message = "; ".join(
                    error["msg"] for error in exc.errors(include_url=False)
                )
            errors.append({"row": line_number, "error": message})
        if len(errors) >= 50:
            break
    if errors:
        raise AppError(
            "Bill CSV validation failed; no rows were imported",
            status_code=422,
            details={"errors": errors, "imported": 0},
        )
    if not prepared:
        raise AppError("CSV contains no data rows", status_code=422)
    db.add_all(prepared)
    db.commit()
    return {"imported": len(prepared), "errors": []}


def comparison_history_rows(db: Session) -> list[dict]:
    rows = db.execute(
        select(BillComparison, ElectricityBill)
        .join(ElectricityBill, BillComparison.bill_id == ElectricityBill.id)
        .order_by(ElectricityBill.billing_period_start.desc())
    ).all()
    return [
        {
            "bill_id": bill.id,
            "bill_reference": bill.bill_reference,
            "billing_period_start": bill.billing_period_start.isoformat(),
            "billing_period_end": bill.billing_period_end.isoformat(),
            "estimated_units": f"{Decimal(comparison.estimated_units):.2f}",
            "actual_units": f"{Decimal(comparison.actual_units):.2f}",
            "estimated_cost": money_str(comparison.estimated_cost),
            "actual_cost": money_str(comparison.actual_cost),
            "cost_deviation": money_str(comparison.cost_deviation),
            "percentage_deviation": (
                f"{Decimal(comparison.percentage_deviation):.2f}"
                if comparison.percentage_deviation is not None
                else None
            ),
            "tolerance_percent": f"{Decimal(comparison.tolerance_percent):.2f}",
            "exceeds_tolerance": comparison.exceeds_tolerance,
            "coverage_pct": f"{Decimal(comparison.data_coverage_pct):.2f}",
        }
        for comparison, bill in rows
    ]
