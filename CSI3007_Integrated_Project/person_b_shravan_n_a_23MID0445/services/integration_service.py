"""Person B → Person A authenticated REST integration."""

from __future__ import annotations

import time
from datetime import date, datetime, timezone
from decimal import Decimal

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database import utcnow
from errors import AppError
from models import IntegrationSyncState, Subscription, SubscriptionPayment
from services.billing import monthly_cost, period_bounds
from services.common import money_str

DESTINATION = "person_a"


def build_sync_payload(db: Session, period: str | None = None) -> dict:
    period = period or date.today().strftime("%Y-%m")
    period_start, period_end = period_bounds(period)
    subscriptions = list(
        db.scalars(
            select(Subscription)
            .where(
                Subscription.status == "active",
                Subscription.start_date <= period_end,
            )
            .order_by(Subscription.service_name)
        ).all()
    )
    records = []
    estimated_records = 0
    actual_records = 0
    by_currency: dict[str, Decimal] = {}
    for subscription in subscriptions:
        payment = db.scalar(
            select(SubscriptionPayment).where(
                SubscriptionPayment.subscription_id == subscription.id,
                SubscriptionPayment.billing_period == period,
            )
        )
        if payment:
            amount = payment.amount
            billing_date = payment.paid_on
            updated_at = payment.created_at
            is_estimate = False
            description = (
                f"Recorded payment for {subscription.service_name} ({period}). "
                "Recorded manually in Person B; no payment provider was called."
            )
            actual_records += 1
        else:
            amount = monthly_cost(
                subscription.amount,
                subscription.billing_cycle,
                subscription.custom_interval_days,
            )
            if period_start <= subscription.next_renewal_date <= period_end:
                billing_date = subscription.next_renewal_date
            else:
                billing_date = period_end
            updated_at = subscription.updated_at
            is_estimate = True
            description = (
                f"Estimated monthly recurring share for {subscription.service_name} "
                f"({period}). Not an actual payment."
            )
            estimated_records += 1
        by_currency[subscription.currency] = (
            by_currency.get(subscription.currency, Decimal("0")) + Decimal(amount)
        )
        records.append(
            {
                "source_app": "person_b",
                "external_id": f"sub:{subscription.id}:{period}",
                "subscription_id": subscription.id,
                "service_name": subscription.service_name,
                "category": subscription.category,
                "amount": money_str(amount),
                "currency": subscription.currency,
                "billing_period": period,
                "billing_date": billing_date.isoformat(),
                "record_updated_at": updated_at.isoformat(),
                "is_estimate": is_estimate,
                "description": description,
            }
        )
    return {
        "source_app": "person_b",
        "generated_at": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "billing_period": period,
        "summary": {
            "active_subscriptions": len(subscriptions),
            "expense_records": len(records),
            "estimated_records": estimated_records,
            "actual_records": actual_records,
            "monthly_costs_by_currency": {
                currency: money_str(total)
                for currency, total in sorted(by_currency.items())
            },
            "note": (
                "Estimated records are recurring-cost shares, not confirmed payments. "
                "No payment provider is integrated."
            ),
        },
        "expense_records": records,
    }


def _get_state(db: Session) -> IntegrationSyncState:
    state = db.scalar(
        select(IntegrationSyncState).where(
            IntegrationSyncState.destination == DESTINATION
        )
    )
    if not state:
        state = IntegrationSyncState(destination=DESTINATION, status="never")
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


def _mark_failure(
    db: Session, message: str, *, period: str, http_status: int | None = None
) -> IntegrationSyncState:
    state = _get_state(db)
    state.status = "failure"
    state.last_attempt_at = utcnow()
    state.last_error = message[:500]
    state.last_period = period
    state.last_http_status = http_status
    db.commit()
    db.refresh(state)
    return state


def _mark_success(
    db: Session, *, period: str, records_sent: int, http_status: int
) -> IntegrationSyncState:
    state = _get_state(db)
    state.status = "success"
    state.last_attempt_at = utcnow()
    state.last_success_at = state.last_attempt_at
    state.last_error = None
    state.records_sent = records_sent
    state.last_period = period
    state.last_http_status = http_status
    db.commit()
    db.refresh(state)
    return state


def push_to_person_a(db: Session, period: str | None = None) -> dict:
    period = period or date.today().strftime("%Y-%m")
    payload = build_sync_payload(db, period)
    url = f"{settings.person_a_api_url.rstrip('/')}/integrations/subscriptions/sync"
    headers = {
        "X-API-Key": settings.person_a_sync_api_key,
        "Content-Type": "application/json",
    }
    last_error = "Person A did not respond"
    last_status: int | None = None
    response = None
    for attempt in range(settings.integration_retries + 1):
        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=settings.integration_timeout_seconds,
            )
            last_status = response.status_code
            if response.status_code >= 500 and attempt < settings.integration_retries:
                time.sleep(0.5 * (attempt + 1))
                continue
            break
        except requests.Timeout:
            last_error = "Person A timed out while receiving subscription data"
        except requests.ConnectionError:
            last_error = "Person A is unreachable; local subscription data is preserved"
        except requests.RequestException:
            last_error = "The request to Person A failed"
        if attempt < settings.integration_retries:
            time.sleep(0.5 * (attempt + 1))
    if response is None or response.status_code != 200:
        if response is not None:
            last_error = f"Person A returned HTTP {response.status_code}"
        _mark_failure(db, last_error, period=period, http_status=last_status)
        raise AppError(
            last_error + ". Local data is unchanged and you can retry the sync.",
            status_code=503,
            details={
                "destination": "person_a",
                "status": "failure",
                "period": period,
                "records_preserved": len(payload["expense_records"]),
            },
        )
    try:
        person_a_response = response.json()
    except ValueError:
        last_error = "Person A returned a non-JSON response"
        _mark_failure(db, last_error, period=period, http_status=last_status)
        raise AppError(last_error, status_code=502)
    state = _mark_success(
        db,
        period=period,
        records_sent=len(payload["expense_records"]),
        http_status=response.status_code,
    )
    return {
        "status": "success",
        "destination": "person_a",
        "period": period,
        "records_sent": len(payload["expense_records"]),
        "last_success_at": state.last_success_at,
        "person_a_response": person_a_response,
    }


def _remote_health() -> dict:
    try:
        response = requests.get(
            f"{settings.person_a_api_url.rstrip('/')}/health",
            timeout=min(2.0, settings.integration_timeout_seconds),
        )
        return {"reachable": response.status_code == 200, "http_status": response.status_code}
    except requests.RequestException:
        return {"reachable": False, "http_status": None}


def integration_status(db: Session, *, check_remote: bool = False) -> dict:
    state = db.scalar(
        select(IntegrationSyncState).where(
            IntegrationSyncState.destination == DESTINATION
        )
    )
    result = {
        "destination": DESTINATION,
        "label": "Person A — Smart Expense Manager",
        "api_url": settings.person_a_api_url,
        "api_key_configured": bool(settings.person_a_sync_api_key),
        "status": state.status if state else "never",
        "last_attempt_at": state.last_attempt_at if state else None,
        "last_success_at": state.last_success_at if state else None,
        "last_error": state.last_error if state else None,
        "records_sent": state.records_sent if state else 0,
        "last_period": state.last_period if state else None,
        "last_http_status": state.last_http_status if state else None,
        "note": (
            "Sync is a manual push. Failures never delete local subscriptions or payments. "
            "The last successful timestamp is retained separately from the last attempt."
        ),
    }
    if check_remote:
        result["remote_health"] = _remote_health()
    return result
