"""Actual payment history with idempotent creation."""

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from errors import AppError
from models import Subscription, SubscriptionPayment
from schemas import PaymentCreate
from services.billing import period_bounds
from services.common import money, money_str


def serialize_payment(payment: SubscriptionPayment) -> dict:
    return {
        "id": payment.id,
        "subscription_id": payment.subscription_id,
        "service_name": payment.subscription.service_name if payment.subscription else None,
        "amount": money_str(payment.amount),
        "currency": payment.currency,
        "paid_on": payment.paid_on,
        "billing_period": payment.billing_period,
        "payment_method": payment.payment_method,
        "reference": payment.reference,
        "notes": payment.notes,
        "idempotency_key": payment.idempotency_key,
        "created_at": payment.created_at,
    }


def create_payment(db: Session, payload: PaymentCreate) -> tuple[SubscriptionPayment, bool]:
    subscription = db.get(Subscription, payload.subscription_id)
    if not subscription:
        raise AppError("Subscription not found", status_code=404)
    if payload.paid_on > date.today():
        raise AppError("A recorded actual payment cannot be dated in the future", 422)
    billing_period = payload.billing_period or payload.paid_on.strftime("%Y-%m")
    period_bounds(billing_period)
    currency = payload.currency or subscription.currency
    if currency != subscription.currency:
        raise AppError("Payment currency must match the subscription currency", 422)
    amount = money(payload.amount)
    idempotency_key = (
        payload.idempotency_key
        or f"payment:{subscription.id}:{billing_period}:{amount:.2f}:{payload.paid_on.isoformat()}"
    )

    existing = db.scalar(
        select(SubscriptionPayment).where(
            SubscriptionPayment.idempotency_key == idempotency_key
        )
    )
    if existing:
        return existing, True
    same_period = db.scalar(
        select(SubscriptionPayment).where(
            SubscriptionPayment.subscription_id == subscription.id,
            SubscriptionPayment.billing_period == billing_period,
        )
    )
    if same_period:
        return same_period, True

    payment = SubscriptionPayment(
        subscription_id=subscription.id,
        amount=amount,
        currency=currency,
        paid_on=payload.paid_on,
        billing_period=billing_period,
        payment_method=payload.payment_method,
        reference=payload.reference,
        notes=payload.notes,
        idempotency_key=idempotency_key,
    )
    db.add(payment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(SubscriptionPayment).where(
                SubscriptionPayment.idempotency_key == idempotency_key
            )
        )
        if existing:
            return existing, True
        raise AppError("That payment was already recorded", status_code=409)
    db.refresh(payment)
    return payment, False


def list_payments(
    db: Session,
    *,
    subscription_id: int | None = None,
    billing_period: str | None = None,
    limit: int = 500,
) -> list[SubscriptionPayment]:
    stmt = select(SubscriptionPayment).order_by(
        SubscriptionPayment.paid_on.desc(), SubscriptionPayment.id.desc()
    )
    if subscription_id:
        stmt = stmt.where(SubscriptionPayment.subscription_id == subscription_id)
    if billing_period:
        period_bounds(billing_period)
        stmt = stmt.where(SubscriptionPayment.billing_period == billing_period)
    return list(db.scalars(stmt.limit(min(max(limit, 1), 2000))).all())


def delete_payment(db: Session, payment_id: int) -> None:
    payment = db.get(SubscriptionPayment, payment_id)
    if not payment:
        raise AppError("Payment not found", status_code=404)
    db.delete(payment)
    db.commit()
