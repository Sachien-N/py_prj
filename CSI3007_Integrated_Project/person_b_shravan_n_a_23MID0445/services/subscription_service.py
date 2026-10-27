"""Subscription CRUD, search, projections and renewal views."""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from errors import AppError
from models import Subscription, SubscriptionPayment
from schemas import SubscriptionCreate, SubscriptionUpdate
from services.billing import (
    annual_cost,
    calculate_next_renewal,
    monthly_cost,
    period_bounds,
)
from services.common import money, money_str

SORT_FIELDS = {
    "service_name": Subscription.service_name,
    "amount": Subscription.amount,
    "next_renewal_date": Subscription.next_renewal_date,
    "created_at": Subscription.created_at,
    "status": Subscription.status,
    "category": Subscription.category,
}


def serialize_subscription(subscription: Subscription) -> dict:
    monthly = monthly_cost(
        subscription.amount, subscription.billing_cycle, subscription.custom_interval_days
    )
    yearly = annual_cost(
        subscription.amount, subscription.billing_cycle, subscription.custom_interval_days
    )
    today = date.today()
    return {
        "id": subscription.id,
        "service_name": subscription.service_name,
        "category": subscription.category,
        "amount": money_str(subscription.amount),
        "currency": subscription.currency,
        "billing_cycle": subscription.billing_cycle,
        "custom_interval_days": subscription.custom_interval_days,
        "start_date": subscription.start_date,
        "next_renewal_date": subscription.next_renewal_date,
        "payment_method": subscription.payment_method,
        "status": subscription.status,
        "notes": subscription.notes,
        "reminder_days_before": subscription.reminder_days_before,
        "monthly_equivalent": money_str(monthly),
        "yearly_equivalent": money_str(yearly),
        "is_overdue": subscription.status == "active"
        and subscription.next_renewal_date < today,
        "days_until_renewal": (subscription.next_renewal_date - today).days,
        "created_at": subscription.created_at,
        "updated_at": subscription.updated_at,
    }


def get_subscription(db: Session, subscription_id: int) -> Subscription:
    subscription = db.get(Subscription, subscription_id)
    if not subscription:
        raise AppError("Subscription not found", status_code=404)
    return subscription


def list_subscriptions(
    db: Session,
    *,
    status: str | None = None,
    category: str | None = None,
    search: str | None = None,
    sort_by: str = "next_renewal_date",
    sort_order: str = "asc",
) -> list[Subscription]:
    stmt = select(Subscription)
    if status:
        stmt = stmt.where(Subscription.status == status)
    if category:
        stmt = stmt.where(func.lower(Subscription.category) == category.lower())
    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Subscription.service_name.ilike(pattern),
                Subscription.category.ilike(pattern),
                Subscription.notes.ilike(pattern),
            )
        )
    column = SORT_FIELDS.get(sort_by)
    if column is None:
        raise AppError("Unsupported sort field", status_code=422)
    stmt = stmt.order_by(column.desc() if sort_order.lower() == "desc" else column.asc())
    return list(db.scalars(stmt).all())


def create_subscription(db: Session, payload: SubscriptionCreate) -> Subscription:
    next_date = payload.next_renewal_date or calculate_next_renewal(
        payload.start_date,
        payload.billing_cycle,
        payload.custom_interval_days,
        after=max(date.today(), payload.start_date),
    )
    subscription = Subscription(
        service_name=payload.service_name,
        category=payload.category,
        amount=money(payload.amount),
        currency=payload.currency,
        billing_cycle=payload.billing_cycle,
        custom_interval_days=payload.custom_interval_days,
        start_date=payload.start_date,
        next_renewal_date=next_date,
        payment_method=payload.payment_method,
        status=payload.status,
        notes=payload.notes,
        reminder_days_before=payload.reminder_days_before,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription


def update_subscription(
    db: Session, subscription_id: int, payload: SubscriptionUpdate
) -> Subscription:
    subscription = get_subscription(db, subscription_id)
    data = payload.model_dump(exclude_unset=True)

    if "currency" in data and data["currency"] != subscription.currency:
        payment_count = db.scalar(
            select(func.count(SubscriptionPayment.id)).where(
                SubscriptionPayment.subscription_id == subscription.id
            )
        )
        if payment_count:
            raise AppError(
                "Currency cannot change after payments have been recorded", status_code=409
            )

    new_cycle = data.get("billing_cycle", subscription.billing_cycle)
    if new_cycle == "custom":
        custom_days = data.get("custom_interval_days", subscription.custom_interval_days)
        if not custom_days:
            raise AppError("A custom cycle requires custom_interval_days", status_code=422)
    else:
        custom_days = None
        if "custom_interval_days" in data and data["custom_interval_days"] is not None:
            raise AppError(
                "custom_interval_days is only valid for a custom billing cycle", 422
            )
    new_start = data.get("start_date", subscription.start_date)
    if "next_renewal_date" in data and data["next_renewal_date"] is not None:
        new_next = data["next_renewal_date"]
    elif (
        "start_date" in data
        or "billing_cycle" in data
        or "custom_interval_days" in data
    ):
        new_next = calculate_next_renewal(
            new_start,
            new_cycle,
            custom_days,
            after=max(date.today(), new_start),
        )
    else:
        new_next = subscription.next_renewal_date
    if new_next < new_start:
        raise AppError("next_renewal_date cannot be before start_date", status_code=422)

    for field in (
        "service_name",
        "category",
        "amount",
        "currency",
        "billing_cycle",
        "start_date",
        "payment_method",
        "status",
        "notes",
        "reminder_days_before",
    ):
        if field in data:
            value = money(data[field]) if field == "amount" else data[field]
            setattr(subscription, field, value)
    subscription.custom_interval_days = custom_days
    previous_next = subscription.next_renewal_date
    subscription.next_renewal_date = new_next
    from services.renewal_service import dismiss_pending_for_subscription

    if subscription.status != "active":
        dismiss_pending_for_subscription(db, subscription.id)
    elif previous_next != subscription.next_renewal_date:
        dismiss_pending_for_subscription(
            db, subscription.id, keep_date=subscription.next_renewal_date
        )
    db.commit()
    db.refresh(subscription)
    return subscription


def delete_subscription(db: Session, subscription_id: int) -> None:
    subscription = get_subscription(db, subscription_id)
    db.delete(subscription)
    db.commit()


def advance_renewal(db: Session, subscription_id: int) -> Subscription:
    from services.billing import next_renewal_after
    from services.renewal_service import dismiss_stale_for_subscription

    subscription = get_subscription(db, subscription_id)
    subscription.next_renewal_date = next_renewal_after(
        subscription.next_renewal_date,
        subscription.billing_cycle,
        subscription.custom_interval_days,
    )
    dismiss_stale_for_subscription(
        db, subscription.id, subscription.next_renewal_date
    )
    db.commit()
    db.refresh(subscription)
    return subscription


def subscription_summary(db: Session) -> dict:
    subscriptions = list(db.scalars(select(Subscription)).all())
    today = date.today()
    current_period = today.strftime("%Y-%m")
    status_counts = {status: 0 for status in ("active", "paused", "cancelled", "expired")}
    for item in subscriptions:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
    active = [item for item in subscriptions if item.status == "active"]

    by_currency: dict[str, dict] = {}
    for item in active:
        bucket = by_currency.setdefault(
            item.currency,
            {
                "currency": item.currency,
                "active_subscriptions": 0,
                "expected_monthly": Decimal("0"),
                "yearly_projection": Decimal("0"),
            },
        )
        bucket["active_subscriptions"] += 1
        bucket["expected_monthly"] += monthly_cost(
            item.amount, item.billing_cycle, item.custom_interval_days
        )
        bucket["yearly_projection"] += annual_cost(
            item.amount, item.billing_cycle, item.custom_interval_days
        )
    for bucket in by_currency.values():
        bucket["expected_monthly"] = money_str(bucket["expected_monthly"])
        bucket["yearly_projection"] = money_str(bucket["yearly_projection"])

    primary = by_currency.get(
        "INR",
        {
            "currency": "INR",
            "active_subscriptions": 0,
            "expected_monthly": "0.00",
            "yearly_projection": "0.00",
        },
    )

    category_buckets: dict[str, dict] = {}
    cycle_buckets: dict[str, dict] = {}
    for item in active:
        if item.currency != "INR":
            continue
        monthly = monthly_cost(
            item.amount, item.billing_cycle, item.custom_interval_days
        )
        category = category_buckets.setdefault(
            item.category, {"category": item.category, "subscriptions": 0, "monthly": Decimal("0")}
        )
        category["subscriptions"] += 1
        category["monthly"] += monthly
        cycle = cycle_buckets.setdefault(
            item.billing_cycle, {"cycle": item.billing_cycle, "subscriptions": 0, "monthly": Decimal("0")}
        )
        cycle["subscriptions"] += 1
        cycle["monthly"] += monthly
    for bucket in category_buckets.values():
        bucket["monthly"] = money_str(bucket["monthly"])
    for bucket in cycle_buckets.values():
        bucket["monthly"] = money_str(bucket["monthly"])

    actual_rows = db.execute(
        select(
            SubscriptionPayment.currency,
            func.coalesce(func.sum(SubscriptionPayment.amount), 0),
            func.count(SubscriptionPayment.id),
        )
        .where(SubscriptionPayment.billing_period == current_period)
        .group_by(SubscriptionPayment.currency)
    ).all()
    actual_by_currency = [
        {"currency": currency, "amount": money_str(total), "count": int(count)}
        for currency, total, count in actual_rows
    ]
    actual_primary = next(
        (item["amount"] for item in actual_by_currency if item["currency"] == "INR"),
        "0.00",
    )
    upcoming_cutoff = today + timedelta(days=30)
    upcoming_count = sum(
        1 for item in active if today <= item.next_renewal_date <= upcoming_cutoff
    )
    overdue_count = sum(1 for item in active if item.next_renewal_date < today)
    next_renewal = min((item.next_renewal_date for item in active), default=None)
    return {
        "currency": "INR",
        "generated_on": today,
        "status_counts": status_counts,
        "active_subscriptions": status_counts["active"],
        "expected_monthly_recurring": primary["expected_monthly"],
        "yearly_projection": primary["yearly_projection"],
        "actual_payments_this_month": actual_primary,
        "actual_payments_by_currency": actual_by_currency,
        "by_currency": sorted(by_currency.values(), key=lambda item: item["currency"]),
        "by_category": sorted(
            category_buckets.values(), key=lambda item: Decimal(item["monthly"]), reverse=True
        ),
        "by_cycle": sorted(cycle_buckets.values(), key=lambda item: item["cycle"]),
        "upcoming_30_days": upcoming_count,
        "overdue": overdue_count,
        "next_renewal_date": next_renewal,
        "note": (
            "Expected recurring costs are estimates derived from billing cycles. Actual payments "
            "are only those recorded manually in the payment history; no payment provider is integrated."
        ),
    }


def upcoming_renewals(db: Session, days: int = 30) -> dict:
    today = date.today()
    cutoff = today + timedelta(days=max(days, 0))
    stmt = (
        select(Subscription)
        .where(
            Subscription.status == "active",
            Subscription.next_renewal_date <= cutoff,
        )
        .order_by(Subscription.next_renewal_date)
    )
    records = list(db.scalars(stmt).all())
    overdue = [item for item in records if item.next_renewal_date < today]
    upcoming = [item for item in records if item.next_renewal_date >= today]
    from services.renewal_service import pending_reminders

    return {
        "as_of": today,
        "horizon_days": max(days, 0),
        "overdue_records": [serialize_subscription(item) for item in overdue],
        "upcoming_records": [serialize_subscription(item) for item in upcoming],
        "reminders": pending_reminders(db),
        "counts": {"overdue": len(overdue), "upcoming": len(upcoming)},
    }


def export_csv(db: Session) -> str:
    items = list_subscriptions(db, sort_by="service_name", sort_order="asc")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "service_name",
            "category",
            "amount",
            "currency",
            "billing_cycle",
            "custom_interval_days",
            "start_date",
            "next_renewal_date",
            "payment_method",
            "status",
            "monthly_equivalent",
            "yearly_equivalent",
            "reminder_days_before",
            "notes",
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.id,
                item.service_name,
                item.category,
                money_str(item.amount),
                item.currency,
                item.billing_cycle,
                item.custom_interval_days or "",
                item.start_date.isoformat(),
                item.next_renewal_date.isoformat(),
                item.payment_method,
                item.status,
                money_str(
                    monthly_cost(
                        item.amount, item.billing_cycle, item.custom_interval_days
                    )
                ),
                money_str(
                    annual_cost(
                        item.amount, item.billing_cycle, item.custom_interval_days
                    )
                ),
                item.reminder_days_before,
                item.notes,
            ]
        )
    return buffer.getvalue()
