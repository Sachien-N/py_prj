"""Person C → Person A authenticated REST integration."""

from __future__ import annotations

import time
from datetime import date
from decimal import Decimal

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database import utcnow
from errors import AppError
from models import IntegrationSyncState
from services.common import dec, money_str
from services.expense_service import build_person_a_payload, default_expense_range

DESTINATION = "person_a"


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
    db: Session,
    message: str,
    *,
    period: str,
    http_status: int | None = None,
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


def push_to_person_a(
    db: Session,
    start_date: date | None = None,
    end_date: date | None = None,
) -> dict:
    if start_date is None or end_date is None:
        default_start, default_end = default_expense_range()
        start_date = start_date or default_start
        end_date = end_date or default_end
    payload = build_person_a_payload(db, start_date, end_date)
    period_label = f"{start_date.isoformat()}..{end_date.isoformat()}"
    url = f"{settings.person_a_api_url.rstrip('/')}/integrations/electricity/sync"
    headers = {
        "X-API-Key": settings.person_a_sync_api_key,
        "Content-Type": "application/json",
    }
    response = None
    last_error = "Person A did not respond"
    last_status: int | None = None
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
            last_error = "Person A timed out while receiving electricity data"
        except requests.ConnectionError:
            last_error = "Person A is unreachable; local electricity data is preserved"
        except requests.RequestException:
            last_error = "The request to Person A failed"
        if attempt < settings.integration_retries:
            time.sleep(0.5 * (attempt + 1))
    if response is None or response.status_code != 200:
        if response is not None:
            last_error = f"Person A returned HTTP {response.status_code}"
        _mark_failure(db, last_error, period=period_label, http_status=last_status)
        raise AppError(
            last_error + ". Local readings and bills are unchanged and you can retry.",
            status_code=503,
            details={
                "destination": "person_a",
                "status": "failure",
                "range": period_label,
                "records_preserved": len(payload["expense_records"]),
            },
        )
    try:
        person_a_response = response.json()
    except ValueError:
        last_error = "Person A returned a non-JSON response"
        _mark_failure(db, last_error, period=period_label, http_status=last_status)
        raise AppError(last_error, status_code=502)
    state = _mark_success(
        db,
        period=period_label,
        records_sent=len(payload["expense_records"]),
        http_status=response.status_code,
    )
    return {
        "status": "success",
        "destination": "person_a",
        "period": period_label,
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
            "A failed sync never deletes local readings or bills. Actual bills take "
            "precedence over estimates in the exported monthly records."
        ),
    }
    if check_remote:
        result["remote_health"] = _remote_health()
    return result
