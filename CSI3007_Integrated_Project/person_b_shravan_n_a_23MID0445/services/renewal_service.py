"""Renewal reminders stored inside Person B's own database."""

from __future__ import annotations

from datetime import date, datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from errors import AppError
from models import RenewalReminder, Subscription


def serialize_reminder(reminder: RenewalReminder) -> dict:
    today = date.today()
    return {
        "id": reminder.id,
        "subscription_id": reminder.subscription_id,
        "service_name": reminder.subscription.service_name
        if reminder.subscription
        else None,
        "renewal_date": reminder.renewal_date,
        "status": reminder.status,
        "days_until_renewal": (reminder.renewal_date - today).days,
        "created_at": reminder.created_at,
        "dismissed_at": reminder.dismissed_at,
    }


def pending_reminders(db: Session) -> list[dict]:
    stmt = (
        select(RenewalReminder)
        .options(joinedload(RenewalReminder.subscription))
        .join(RenewalReminder.subscription)
        .where(
            RenewalReminder.status == "pending",
            Subscription.status == "active",
        )
        .order_by(RenewalReminder.renewal_date)
    )
    return [serialize_reminder(item) for item in db.scalars(stmt).unique().all()]


def refresh_reminders(db: Session) -> dict:
    today = date.today()
    created = 0
    subscriptions = list(
        db.scalars(select(Subscription).where(Subscription.status == "active")).all()
    )
    for subscription in subscriptions:
        horizon = today + timedelta(days=subscription.reminder_days_before)
        if subscription.next_renewal_date > horizon:
            continue
        existing = db.scalar(
            select(RenewalReminder).where(
                RenewalReminder.subscription_id == subscription.id,
                RenewalReminder.renewal_date == subscription.next_renewal_date,
            )
        )
        if existing:
            continue
        db.add(
            RenewalReminder(
                subscription_id=subscription.id,
                renewal_date=subscription.next_renewal_date,
                status="pending",
            )
        )
        created += 1
    db.commit()
    return {
        "created": created,
        "pending": pending_reminders(db),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def dismiss_reminder(db: Session, reminder_id: int) -> RenewalReminder:
    reminder = db.get(RenewalReminder, reminder_id)
    if not reminder:
        raise AppError("Reminder not found", status_code=404)
    reminder.status = "dismissed"
    reminder.dismissed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(reminder)
    return reminder


def dismiss_pending_for_subscription(
    db: Session, subscription_id: int, *, keep_date: date | None = None
) -> None:
    stmt = select(RenewalReminder).where(
        RenewalReminder.subscription_id == subscription_id,
        RenewalReminder.status == "pending",
    )
    if keep_date is not None:
        stmt = stmt.where(RenewalReminder.renewal_date != keep_date)
    reminders = db.scalars(stmt).all()
    for reminder in reminders:
        reminder.status = "dismissed"
        reminder.dismissed_at = datetime.now(timezone.utc).replace(tzinfo=None)


def dismiss_stale_for_subscription(
    db: Session, subscription_id: int, new_renewal_date: date
) -> None:
    dismiss_pending_for_subscription(
        db, subscription_id, keep_date=new_renewal_date
    )
