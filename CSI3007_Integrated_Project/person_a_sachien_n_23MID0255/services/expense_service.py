"""Expense CRUD, filtering, refund validation, and summaries."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from errors import AppError
from models import Category, Expense
from schemas import ExpenseCreate, ExpenseUpdate
from services.category_service import categorize_merchant, require_category
from services.common import money, money_str


def serialize_expense(expense: Expense) -> dict:
    return {
        "id": expense.id,
        "amount": money_str(expense.amount),
        "currency": expense.currency,
        "expense_date": expense.expense_date,
        "merchant": expense.merchant,
        "category_id": expense.category_id,
        "category": expense.category.name if expense.category else None,
        "payment_method": expense.payment_method,
        "description": expense.description,
        "transaction_type": expense.transaction_type,
        "refund_of_expense_id": expense.refund_of_expense_id,
        "source_app": expense.source_app,
        "external_id": expense.external_id,
        "is_estimated": expense.is_estimated,
        "created_at": expense.created_at,
        "updated_at": expense.updated_at,
    }


def get_expense(db: Session, expense_id: int) -> Expense:
    expense = db.scalar(
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.id == expense_id)
    )
    if not expense:
        raise AppError("Expense not found", status_code=404)
    return expense


def list_expenses(
    db: Session,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    category: str | None = None,
    search: str | None = None,
    transaction_type: str | None = None,
    source_app: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[Expense]:
    if start_date and end_date and start_date > end_date:
        raise AppError("start_date cannot be after end_date", status_code=422)
    stmt = select(Expense).options(joinedload(Expense.category))
    if start_date:
        stmt = stmt.where(Expense.expense_date >= start_date)
    if end_date:
        stmt = stmt.where(Expense.expense_date <= end_date)
    if category:
        stmt = stmt.join(Expense.category).where(
            func.lower(Category.name) == category.strip().lower()
        )
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Expense.merchant.ilike(pattern),
                Expense.description.ilike(pattern),
            )
        )
    if transaction_type:
        stmt = stmt.where(Expense.transaction_type == transaction_type)
    if source_app:
        stmt = stmt.where(Expense.source_app == source_app)
    stmt = (
        stmt.order_by(Expense.expense_date.desc(), Expense.id.desc())
        .limit(min(max(limit, 1), 2000))
        .offset(max(offset, 0))
    )
    return list(db.scalars(stmt).unique().all())


def _category_for_new(db: Session, payload: ExpenseCreate) -> int:
    if payload.category:
        return require_category(db, payload.category).id
    if not payload.auto_categorize:
        raise AppError("A category is required when auto_categorize is false", 422)
    category = categorize_merchant(db, payload.merchant, payload.description)
    return category.id


def _validate_refund(
    db: Session,
    *,
    refund_of_expense_id: int | None,
    amount: Decimal,
    currency: str,
    exclude_refund_id: int | None = None,
) -> None:
    if not refund_of_expense_id:
        return
    original = db.get(Expense, refund_of_expense_id)
    if not original:
        raise AppError("The original expense for this refund was not found", 404)
    if original.transaction_type != "expense":
        raise AppError("A refund can only reference an expense record", 422)
    if original.currency != currency:
        raise AppError("Refund currency must match the original expense", 422)
    stmt = select(func.coalesce(func.sum(Expense.amount), 0)).where(
        Expense.refund_of_expense_id == refund_of_expense_id,
        Expense.transaction_type == "refund",
    )
    if exclude_refund_id is not None:
        stmt = stmt.where(Expense.id != exclude_refund_id)
    already_refunded = money(db.scalar(stmt) or 0)
    if already_refunded + amount > money(original.amount):
        raise AppError(
            "Refund total cannot exceed the original expense amount", status_code=422
        )


def create_expense(db: Session, payload: ExpenseCreate, *, commit: bool = True) -> Expense:
    category_id = _category_for_new(db, payload)
    if payload.transaction_type == "refund":
        _validate_refund(
            db,
            refund_of_expense_id=payload.refund_of_expense_id,
            amount=money(payload.amount),
            currency=payload.currency,
        )
    expense = Expense(
        amount=money(payload.amount),
        currency=payload.currency,
        expense_date=payload.expense_date,
        merchant=payload.merchant,
        category_id=category_id,
        payment_method=payload.payment_method,
        description=payload.description,
        transaction_type=payload.transaction_type,
        refund_of_expense_id=payload.refund_of_expense_id,
        source_app="local",
        external_id=None,
        is_estimated=False,
    )
    db.add(expense)
    if commit:
        db.commit()
        db.refresh(expense)
    else:
        db.flush()
    return expense


def update_expense(db: Session, expense_id: int, payload: ExpenseUpdate) -> Expense:
    expense = get_expense(db, expense_id)
    data = payload.model_dump(exclude_unset=True)
    if expense.source_app != "local":
        raise AppError(
            "Imported external expenses are read-only here; update them at the source application",
            status_code=409,
        )

    new_type = data.get("transaction_type", expense.transaction_type)
    new_amount = money(data.get("amount", expense.amount))
    new_currency = data.get("currency", expense.currency)
    new_refund_ref = data.get("refund_of_expense_id", expense.refund_of_expense_id)
    if new_type == "expense":
        if new_refund_ref is not None:
            raise AppError("refund_of_expense_id is only valid for refunds", 422)
        refunded = db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).where(
                Expense.refund_of_expense_id == expense.id,
                Expense.transaction_type == "refund",
            )
        )
        if money(refunded or 0) > new_amount:
            raise AppError(
                "Expense amount cannot be lower than refunds already recorded against it",
                422,
            )
    else:
        _validate_refund(
            db,
            refund_of_expense_id=new_refund_ref,
            amount=new_amount,
            currency=new_currency,
            exclude_refund_id=expense.id,
        )

    category_changed = "category" in data
    if category_changed:
        if data["category"]:
            expense.category_id = require_category(db, data["category"]).id
        elif data.get("auto_categorize", True):
            expense.category_id = categorize_merchant(
                db,
                data.get("merchant", expense.merchant),
                data.get("description", expense.description),
            ).id
        else:
            raise AppError("A category is required when auto_categorize is false", 422)

    for field in (
        "amount",
        "currency",
        "expense_date",
        "merchant",
        "payment_method",
        "description",
        "transaction_type",
        "refund_of_expense_id",
    ):
        if field in data:
            value = data[field]
            if field == "amount":
                value = new_amount
            setattr(expense, field, value)
    db.commit()
    db.refresh(expense)
    return expense


def delete_expense(db: Session, expense_id: int) -> None:
    expense = get_expense(db, expense_id)
    if expense.source_app != "local":
        raise AppError(
            "Imported external expenses cannot be deleted here; remove them at the source",
            status_code=409,
        )
    db.delete(expense)
    db.commit()


def expense_summary(
    db: Session,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    currency: str = "INR",
) -> dict:
    if start_date and end_date and start_date > end_date:
        raise AppError("start_date cannot be after end_date", status_code=422)
    currency = currency.upper()
    filters = []
    if start_date:
        filters.append(Expense.expense_date >= start_date)
    if end_date:
        filters.append(Expense.expense_date <= end_date)

    # Totals by currency and transaction type (kept separate: no implicit FX conversion).
    rows = db.execute(
        select(
            Expense.currency,
            Expense.transaction_type,
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        )
        .where(*filters)
        .group_by(Expense.currency, Expense.transaction_type)
    ).all()
    by_currency: dict[str, dict] = {}
    for cur, tx_type, total, count in rows:
        bucket = by_currency.setdefault(
            cur,
            {
                "currency": cur,
                "total_expenses": Decimal("0"),
                "total_refunds": Decimal("0"),
                "net_spending": Decimal("0"),
                "transaction_count": 0,
            },
        )
        if tx_type == "refund":
            bucket["total_refunds"] += money(total)
        else:
            bucket["total_expenses"] += money(total)
        bucket["transaction_count"] += int(count)

    primary = by_currency.get(
        currency,
        {
            "currency": currency,
            "total_expenses": Decimal("0"),
            "total_refunds": Decimal("0"),
            "net_spending": Decimal("0"),
            "transaction_count": 0,
        },
    )
    primary["net_spending"] = primary["total_expenses"] - primary["total_refunds"]
    for bucket in by_currency.values():
        bucket["net_spending"] = bucket["total_expenses"] - bucket["total_refunds"]
        for key in ("total_expenses", "total_refunds", "net_spending"):
            bucket[key] = money_str(bucket[key])

    cat_rows = db.execute(
        select(
            Category.name,
            Category.color,
            Expense.transaction_type,
            func.coalesce(func.sum(Expense.amount), 0),
        )
        .join(Expense, Expense.category_id == Category.id)
        .where(*filters, Expense.currency == currency)
        .group_by(Category.name, Category.color, Expense.transaction_type)
    ).all()
    category_map: dict[str, dict] = {}
    for name, color, tx_type, total in cat_rows:
        item = category_map.setdefault(
            name,
            {
                "category": name,
                "color": color,
                "expense": Decimal("0"),
                "refund": Decimal("0"),
                "net": Decimal("0"),
            },
        )
        if tx_type == "refund":
            item["refund"] += money(total)
        else:
            item["expense"] += money(total)
    for item in category_map.values():
        item["net"] = item["expense"] - item["refund"]
        item["expense"] = money_str(item["expense"])
        item["refund"] = money_str(item["refund"])
        item["net"] = money_str(item["net"])

    payment_rows = db.execute(
        select(
            Expense.payment_method,
            Expense.transaction_type,
            func.coalesce(func.sum(Expense.amount), 0),
        )
        .where(*filters, Expense.currency == currency)
        .group_by(Expense.payment_method, Expense.transaction_type)
    ).all()
    payment_map: dict[str, dict] = {}
    for method, tx_type, total in payment_rows:
        item = payment_map.setdefault(method, {"method": method, "net": Decimal("0")})
        item["net"] += money(total) if tx_type == "expense" else -money(total)
    for item in payment_map.values():
        item["net"] = money_str(item["net"])

    source_rows = db.execute(
        select(
            Expense.source_app,
            Expense.transaction_type,
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        )
        .where(*filters, Expense.currency == currency)
        .group_by(Expense.source_app, Expense.transaction_type)
    ).all()
    source_map: dict[str, dict] = {}
    for source, tx_type, total, count in source_rows:
        item = source_map.setdefault(
            source, {"source_app": source, "net": Decimal("0"), "count": 0}
        )
        item["net"] += money(total) if tx_type == "expense" else -money(total)
        item["count"] += int(count)
    for item in source_map.values():
        item["net"] = money_str(item["net"])

    integrated_rows = db.execute(
        select(
            Expense.source_app,
            func.coalesce(func.sum(Expense.amount), 0),
            func.count(Expense.id),
        )
        .where(
            *filters,
            Expense.currency == currency,
            Expense.source_app != "local",
            Expense.transaction_type == "expense",
        )
        .group_by(Expense.source_app)
    ).all()
    integrated = [
        {"source_app": source, "total": money_str(total), "count": int(count)}
        for source, total, count in integrated_rows
    ]

    return {
        "start_date": start_date,
        "end_date": end_date,
        "currency": currency,
        "total_expenses": money_str(primary["total_expenses"]),
        "total_refunds": money_str(primary["total_refunds"]),
        "net_spending": money_str(primary["net_spending"]),
        "transaction_count": primary["transaction_count"],
        "by_currency": sorted(by_currency.values(), key=lambda item: item["currency"]),
        "by_category": sorted(
            category_map.values(), key=lambda item: Decimal(item["expense"]), reverse=True
        ),
        "by_payment_method": sorted(payment_map.values(), key=lambda item: item["method"]),
        "by_source": sorted(source_map.values(), key=lambda item: item["source_app"]),
        "integrated": integrated,
    }


def daily_trend(
    db: Session,
    *,
    start_date: date,
    end_date: date,
    currency: str = "INR",
) -> list[dict]:
    rows = db.execute(
        select(
            Expense.expense_date,
            Expense.transaction_type,
            func.coalesce(func.sum(Expense.amount), 0),
        )
        .where(
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
            Expense.currency == currency,
        )
        .group_by(Expense.expense_date, Expense.transaction_type)
        .order_by(Expense.expense_date)
    ).all()
    days: dict[date, dict] = {}
    for day, tx_type, total in rows:
        item = days.setdefault(
            day, {"date": day, "expenses": Decimal("0"), "refunds": Decimal("0")}
        )
        if tx_type == "refund":
            item["refunds"] += money(total)
        else:
            item["expenses"] += money(total)
    result = []
    for item in days.values():
        result.append(
            {
                "date": item["date"],
                "expenses": money_str(item["expenses"]),
                "refunds": money_str(item["refunds"]),
                "net": money_str(item["expenses"] - item["refunds"]),
            }
        )
    return result
