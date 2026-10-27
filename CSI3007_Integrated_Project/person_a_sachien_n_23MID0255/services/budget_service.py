"""Monthly overall/category budgets and usage calculations."""

from __future__ import annotations

import calendar
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from errors import AppError
from models import Budget, Category, Expense
from schemas import BudgetCreate, BudgetUpdate
from services.category_service import require_category
from services.common import money, money_str


def month_bounds(month: str) -> tuple[date, date]:
    year, month_number = map(int, month.split("-"))
    last_day = calendar.monthrange(year, month_number)[1]
    return date(year, month_number, 1), date(year, month_number, last_day)


def _spent(
    db: Session, *, month: str, category_id: int | None, currency: str = "INR"
) -> Decimal:
    start, end = month_bounds(month)
    filters = [
        Expense.expense_date >= start,
        Expense.expense_date <= end,
        Expense.currency == currency,
    ]
    if category_id is not None:
        filters.append(Expense.category_id == category_id)
    rows = db.execute(
        select(Expense.transaction_type, func.coalesce(func.sum(Expense.amount), 0))
        .where(*filters)
        .group_by(Expense.transaction_type)
    ).all()
    total = Decimal("0")
    for tx_type, amount in rows:
        total += money(amount) if tx_type == "expense" else -money(amount)
    return total


def serialize_budget(db: Session, budget: Budget) -> dict:
    spent = _spent(db, month=budget.month, category_id=budget.category_id)
    amount = money(budget.amount)
    remaining = amount - spent
    usage = (
        (spent / amount * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if amount
        else Decimal("0")
    )
    return {
        "id": budget.id,
        "month": budget.month,
        "category_id": budget.category_id,
        "category": budget.category.name if budget.category else None,
        "scope": "overall" if budget.category_id is None else "category",
        "amount": money_str(amount),
        "spent": money_str(spent),
        "remaining": money_str(remaining),
        "usage_percent": float(usage),
        "exceeded": spent > amount,
        "notes": budget.notes,
        "created_at": budget.created_at,
        "updated_at": budget.updated_at,
    }


def list_budgets(db: Session, month: str | None = None) -> list[Budget]:
    stmt = select(Budget).options(joinedload(Budget.category))
    if month:
        month_bounds(month)  # validates
        stmt = stmt.where(Budget.month == month)
    stmt = stmt.order_by(Budget.month.desc(), Budget.category_id.is_not(None), Budget.id)
    return list(db.scalars(stmt).unique().all())


def _ensure_unique(
    db: Session, month: str, category_id: int | None, exclude_id: int | None = None
) -> None:
    stmt = select(Budget).where(Budget.month == month)
    if category_id is None:
        stmt = stmt.where(Budget.category_id.is_(None))
    else:
        stmt = stmt.where(Budget.category_id == category_id)
    if exclude_id is not None:
        stmt = stmt.where(Budget.id != exclude_id)
    if db.scalar(stmt):
        raise AppError(
            "A budget already exists for that month and scope", status_code=409
        )


def create_budget(db: Session, payload: BudgetCreate) -> Budget:
    month_bounds(payload.month)
    category_id = require_category(db, payload.category).id if payload.category else None
    _ensure_unique(db, payload.month, category_id)
    budget = Budget(
        month=payload.month,
        category_id=category_id,
        amount=money(payload.amount),
        notes=payload.notes,
    )
    db.add(budget)
    db.commit()
    db.refresh(budget)
    db.expire(budget, ["category"])
    return budget


def update_budget(db: Session, budget_id: int, payload: BudgetUpdate) -> Budget:
    budget = db.get(Budget, budget_id)
    if not budget:
        raise AppError("Budget not found", status_code=404)
    data = payload.model_dump(exclude_unset=True)
    if "category" in data:
        category_id = (
            require_category(db, data["category"]).id if data["category"] else None
        )
        _ensure_unique(db, budget.month, category_id, exclude_id=budget.id)
        budget.category_id = category_id
    if "amount" in data and data["amount"] is not None:
        budget.amount = money(data["amount"])
    if "notes" in data and data["notes"] is not None:
        budget.notes = data["notes"]
    db.commit()
    db.refresh(budget)
    db.expire(budget, ["category"])
    return budget


def delete_budget(db: Session, budget_id: int) -> None:
    budget = db.get(Budget, budget_id)
    if not budget:
        raise AppError("Budget not found", status_code=404)
    db.delete(budget)
    db.commit()


def budget_overview(db: Session, month: str) -> dict:
    budgets = [serialize_budget(db, item) for item in list_budgets(db, month)]
    overall = next((item for item in budgets if item["scope"] == "overall"), None)
    if overall:
        total_budget = Decimal(overall["amount"])
        total_spent = Decimal(overall["spent"])
    else:
        total_budget = sum(
            (Decimal(item["amount"]) for item in budgets), start=Decimal("0")
        )
        total_spent = _spent(db, month=month, category_id=None)
    remaining = total_budget - total_spent
    usage = (
        (total_spent / total_budget * 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if total_budget
        else Decimal("0")
    )
    return {
        "month": month,
        "budget_count": len(budgets),
        "budget_source": "overall" if overall else "category_sum",
        "total_budget": money_str(total_budget),
        "total_spent": money_str(total_spent),
        "remaining": money_str(remaining),
        "usage_percent": float(usage),
        "exceeded": total_budget > 0 and total_spent > total_budget,
        "alerts": [item for item in budgets if item["exceeded"]],
        "budgets": budgets,
    }
