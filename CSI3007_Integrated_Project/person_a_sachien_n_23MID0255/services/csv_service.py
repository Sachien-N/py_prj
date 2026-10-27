"""Validated CSV import and safe CSV export for expenses."""

from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation

from pydantic import ValidationError
from sqlalchemy.orm import Session

from errors import AppError
from models import Expense
from schemas import ExpenseCreate
from services.category_service import categorize_merchant, require_category
from services.common import money
from services.expense_service import list_expenses, serialize_expense

MAX_ROWS = 5000
REQUIRED_HEADERS = {"date", "amount", "merchant"}
KNOWN_HEADERS = {
    "date",
    "amount",
    "merchant",
    "category",
    "payment_method",
    "description",
    "transaction_type",
    "currency",
}


def _safe_cell(value) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\x00", "")
    if text.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text


def export_csv(db: Session, **filters) -> str:
    rows = list_expenses(db, limit=2000, **filters)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "date",
            "amount",
            "currency",
            "merchant",
            "category",
            "payment_method",
            "transaction_type",
            "description",
            "source_app",
            "is_estimated",
        ]
    )
    for item in rows:
        writer.writerow(
            [
                item.id,
                item.expense_date.isoformat(),
                f"{money(item.amount):.2f}",
                item.currency,
                _safe_cell(item.merchant),
                _safe_cell(item.category.name if item.category else ""),
                item.payment_method,
                item.transaction_type,
                _safe_cell(item.description),
                item.source_app,
                "true" if item.is_estimated else "false",
            ]
        )
    return buffer.getvalue()


def import_csv(db: Session, raw: bytes) -> dict:
    if len(raw) > 2 * 1024 * 1024:
        raise AppError("CSV file is larger than the 2 MB limit", status_code=413)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise AppError("CSV must be UTF-8 encoded", status_code=422)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise AppError("CSV has no header row", status_code=422)
    normalized_headers = {header.strip().lower() for header in reader.fieldnames if header}
    missing = REQUIRED_HEADERS - normalized_headers
    if missing:
        raise AppError(
            "CSV is missing required columns: " + ", ".join(sorted(missing)),
            status_code=422,
        )
    unknown = normalized_headers - KNOWN_HEADERS
    if unknown:
        raise AppError(
            "CSV contains unsupported columns: " + ", ".join(sorted(unknown)),
            status_code=422,
        )
    if len(text) > 2 * 1024 * 1024:
        raise AppError("CSV is too large", status_code=413)

    errors: list[dict] = []
    prepared: list[Expense] = []
    seen_rows: set[tuple] = set()
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
            amount = Decimal(row.get("amount", ""))
            if amount <= 0:
                raise ValueError("amount must be positive")
            expense_date = date.fromisoformat(row.get("date", ""))
            payload = ExpenseCreate(
                amount=amount,
                expense_date=expense_date,
                merchant=row.get("merchant", ""),
                category=row.get("category") or None,
                payment_method=row.get("payment_method") or "other",
                description=row.get("description", ""),
                transaction_type=row.get("transaction_type") or "expense",
                currency=row.get("currency") or "INR",
            )
            signature = (
                payload.expense_date,
                money(payload.amount),
                payload.merchant.lower(),
                payload.description.lower(),
            )
            if signature in seen_rows:
                raise ValueError("duplicate row within this CSV")
            seen_rows.add(signature)
            if payload.category:
                category_id = require_category(db, payload.category).id
            else:
                category_id = categorize_merchant(
                    db, payload.merchant, payload.description
                ).id
            prepared.append(
                Expense(
                    amount=money(payload.amount),
                    currency=payload.currency,
                    expense_date=payload.expense_date,
                    merchant=payload.merchant,
                    category_id=category_id,
                    payment_method=payload.payment_method,
                    description=payload.description,
                    transaction_type=payload.transaction_type,
                    source_app="local",
                    external_id=None,
                    is_estimated=False,
                )
            )
        except (ValidationError, ValueError, InvalidOperation) as exc:
            message = str(exc)
            if isinstance(exc, ValidationError):
                message = "; ".join(
                    error["msg"] for error in exc.errors(include_url=False)
                )
            errors.append({"row": line_number, "error": message})
        except AppError as exc:
            errors.append({"row": line_number, "error": exc.message})
        if len(errors) >= 50:
            break

    if errors:
        raise AppError(
            "CSV validation failed; no rows were imported",
            status_code=422,
            details={"errors": errors, "imported": 0},
        )
    if not prepared:
        raise AppError("CSV contains no data rows", status_code=422)
    db.add_all(prepared)
    db.commit()
    return {
        "imported": len(prepared),
        "errors": [],
        "message": f"Imported {len(prepared)} expenses",
    }


def expense_csv_row(item: Expense) -> dict:
    return {
        **serialize_expense(item),
        "date": item.expense_date.isoformat(),
        "category_name": item.category.name if item.category else "",
    }
