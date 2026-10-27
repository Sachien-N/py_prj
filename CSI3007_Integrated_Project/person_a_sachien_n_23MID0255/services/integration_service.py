"""Authenticated, idempotent REST integration with Person B and Person C.

Person A never opens another project's database. It either receives a signed
JSON push or fetches a documented JSON payload over HTTP.
"""

from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone

import requests
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database import utcnow
from errors import AppError
from models import Expense, ImportedExternalExpense, IntegrationSyncState
from schemas import (
    ElectricityExpenseRecord,
    ElectricitySyncRequest,
    SubscriptionExpenseRecord,
    SubscriptionSyncRequest,
)
from services.category_service import get_or_create_external_category
from services.common import money, money_str

SOURCE_LABELS = {
    "person_b": "Person B — Smart Subscription Manager",
    "person_c": "Person C — Smart Electricity Monitoring",
}


def _failure_state(db: Session, source: str, message: str) -> IntegrationSyncState:
    state = db.scalar(
        select(IntegrationSyncState).where(IntegrationSyncState.source == source)
    )
    if not state:
        state = IntegrationSyncState(source=source)
        db.add(state)
    state.status = "failure"
    state.last_attempt_at = utcnow()
    state.last_error = message[:500]
    db.commit()
    db.refresh(state)
    return state


def _success_state(
    db: Session,
    source: str,
    *,
    received: int,
    imported: int,
    updated: int,
    message: str = "",
) -> IntegrationSyncState:
    state = db.scalar(
        select(IntegrationSyncState).where(IntegrationSyncState.source == source)
    )
    if not state:
        state = IntegrationSyncState(source=source)
        db.add(state)
    state.status = "success"
    state.last_attempt_at = utcnow()
    state.last_success_at = state.last_attempt_at
    state.last_error = None
    state.items_received = received
    state.items_imported = imported
    state.items_updated = updated
    if message:
        state.last_error = message[:500]
    db.commit()
    db.refresh(state)
    return state


def _request_json(url: str, api_key: str, *, timeout: float, retries: int) -> dict:
    last_error = "The remote service did not respond"
    for attempt in range(retries + 1):
        try:
            response = requests.get(
                url,
                headers={"X-API-Key": api_key, "Accept": "application/json"},
                timeout=timeout,
            )
            if response.status_code >= 500 and attempt < retries:
                time.sleep(0.4 * (attempt + 1))
                continue
            if response.status_code == 401:
                raise AppError(
                    "The remote service rejected the configured integration API key",
                    status_code=502,
                )
            if response.status_code != 200:
                raise AppError(
                    f"The remote service returned HTTP {response.status_code}",
                    status_code=502,
                )
            try:
                return response.json()
            except ValueError:
                raise AppError(
                    "The remote service returned a non-JSON response", status_code=502
                )
        except requests.Timeout:
            last_error = "The remote service timed out"
        except requests.ConnectionError:
            last_error = "The remote service is unreachable"
        except requests.RequestException:
            last_error = "The remote request failed"
        if attempt < retries:
            time.sleep(0.4 * (attempt + 1))
    raise AppError(last_error, status_code=503)


def _hash_record(record: dict) -> str:
    encoded = json.dumps(record, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _upsert_external_expense(
    db: Session,
    *,
    source: str,
    external_id: str,
    amount,
    currency: str,
    expense_date,
    merchant: str,
    category_name: str,
    description: str,
    is_estimated: bool,
    record_hash: str,
) -> tuple[Expense, bool]:
    existing = db.scalar(
        select(Expense).where(
            Expense.source_app == source, Expense.external_id == external_id
        )
    )
    category = get_or_create_external_category(db, category_name)
    if existing:
        existing.amount = money(amount)
        existing.currency = currency
        existing.expense_date = expense_date
        existing.merchant = merchant
        existing.category_id = category.id
        existing.description = description
        existing.is_estimated = is_estimated
        existing.transaction_type = "expense"
        expense = existing
        created = False
    else:
        expense = Expense(
            amount=money(amount),
            currency=currency,
            expense_date=expense_date,
            merchant=merchant,
            category_id=category.id,
            payment_method="other",
            description=description,
            transaction_type="expense",
            source_app=source,
            external_id=external_id,
            is_estimated=is_estimated,
        )
        db.add(expense)
        db.flush()
        created = True
    mapping = db.scalar(
        select(ImportedExternalExpense).where(
            ImportedExternalExpense.source_app == source,
            ImportedExternalExpense.external_id == external_id,
        )
    )
    if mapping:
        mapping.expense_id = expense.id
        mapping.payload_hash = record_hash
    else:
        db.add(
            ImportedExternalExpense(
                source_app=source,
                external_id=external_id,
                expense_id=expense.id,
                payload_hash=record_hash,
            )
        )
    return expense, created


def _import_subscription_records(
    db: Session, records: list[SubscriptionExpenseRecord]
) -> tuple[int, int]:
    imported = 0
    updated = 0
    seen: set[str] = set()
    for record in records:
        if record.external_id in seen:
            continue
        seen.add(record.external_id)
        _, created = _upsert_external_expense(
            db,
            source="person_b",
            external_id=record.external_id,
            amount=record.amount,
            currency=record.currency,
            expense_date=record.billing_date,
            merchant=record.service_name,
            category_name=record.category,
            description=record.description
            or f"Subscription {record.service_name} for {record.billing_period}",
            is_estimated=record.is_estimate,
            record_hash=_hash_record(record.model_dump(mode="json")),
        )
        imported += int(created)
        updated += int(not created)
    db.commit()
    return imported, updated


def _import_electricity_records(
    db: Session, records: list[ElectricityExpenseRecord]
) -> tuple[int, int]:
    imported = 0
    updated = 0
    seen: set[str] = set()
    for record in records:
        if record.external_id in seen:
            continue
        seen.add(record.external_id)
        units = (
            f" Billed/estimated units: {record.units}."
            if record.units is not None
            else ""
        )
        _, created = _upsert_external_expense(
            db,
            source="person_c",
            external_id=record.external_id,
            amount=record.expense_amount,
            currency=record.currency,
            expense_date=record.billing_date,
            merchant="Electricity — Smart Electricity project",
            category_name="Utilities",
            description=(
                record.description
                or f"Electricity expense for {record.period}.{units}"
            ).strip(),
            is_estimated=record.is_estimate,
            record_hash=_hash_record(record.model_dump(mode="json")),
        )
        imported += int(created)
        updated += int(not created)
    db.commit()
    return imported, updated


def sync_subscriptions(
    db: Session, payload: SubscriptionSyncRequest | None = None
) -> dict:
    source = "person_b"
    if payload is None:
        try:
            data = _request_json(
                f"{settings.person_b_api_url.rstrip('/')}/integrations/person-a/payload",
                settings.person_b_sync_api_key,
                timeout=settings.integration_timeout_seconds,
                retries=settings.integration_retries,
            )
            payload = SubscriptionSyncRequest.model_validate(data)
        except ValidationError:
            message = "Person B returned a payload that failed schema validation"
            _failure_state(db, source, message)
            raise AppError(message, status_code=502)
        except AppError as exc:
            _failure_state(db, source, exc.message)
            raise
    try:
        imported, updated = _import_subscription_records(db, payload.expense_records)
    except Exception:
        db.rollback()
        message = "Person B data could not be imported"
        _failure_state(db, source, message)
        raise AppError(message, status_code=500)
    state = _success_state(
        db,
        source,
        received=len(payload.expense_records),
        imported=imported,
        updated=updated,
    )
    return {
        "source": source,
        "status": "success",
        "billing_period": payload.billing_period,
        "records_received": len(payload.expense_records),
        "records_imported": imported,
        "records_updated": updated,
        "last_success_at": state.last_success_at,
        "message": "Subscription expenses imported idempotently",
    }


def sync_electricity(
    db: Session, payload: ElectricitySyncRequest | None = None
) -> dict:
    source = "person_c"
    if payload is None:
        try:
            data = _request_json(
                f"{settings.person_c_api_url.rstrip('/')}/integrations/person-a/payload",
                settings.person_c_sync_api_key,
                timeout=settings.integration_timeout_seconds,
                retries=settings.integration_retries,
            )
            payload = ElectricitySyncRequest.model_validate(data)
        except ValidationError:
            message = "Person C returned a payload that failed schema validation"
            _failure_state(db, source, message)
            raise AppError(message, status_code=502)
        except AppError as exc:
            _failure_state(db, source, exc.message)
            raise
    try:
        imported, updated = _import_electricity_records(db, payload.expense_records)
    except Exception:
        db.rollback()
        message = "Person C data could not be imported"
        _failure_state(db, source, message)
        raise AppError(message, status_code=500)
    state = _success_state(
        db,
        source,
        received=len(payload.expense_records),
        imported=imported,
        updated=updated,
    )
    return {
        "source": source,
        "status": "success",
        "records_received": len(payload.expense_records),
        "records_imported": imported,
        "records_updated": updated,
        "last_success_at": state.last_success_at,
        "message": "Electricity expenses imported idempotently",
    }


def _serialize_state(state: IntegrationSyncState | None, source: str) -> dict:
    return {
        "source": source,
        "label": SOURCE_LABELS[source],
        "status": state.status if state else "never",
        "last_attempt_at": state.last_attempt_at if state else None,
        "last_success_at": state.last_success_at if state else None,
        "last_error": state.last_error if state else None,
        "items_received": state.items_received if state else 0,
        "items_imported": state.items_imported if state else 0,
        "items_updated": state.items_updated if state else 0,
    }


def _remote_health(url: str) -> dict:
    try:
        response = requests.get(
            f"{url.rstrip('/')}/health", timeout=min(2.0, settings.integration_timeout_seconds)
        )
        return {
            "reachable": response.status_code == 200,
            "http_status": response.status_code,
        }
    except requests.RequestException:
        return {"reachable": False, "http_status": None}


def integration_status(db: Session, *, check_remote: bool = False) -> dict:
    states = {
        state.source: state for state in db.scalars(select(IntegrationSyncState)).all()
    }
    sources = []
    for source in ("person_b", "person_c"):
        item = _serialize_state(states.get(source), source)
        if source == "person_b":
            item["api_url"] = settings.person_b_api_url
            item["api_key_configured"] = bool(settings.person_b_sync_api_key)
            if check_remote:
                item["remote_health"] = _remote_health(settings.person_b_api_url)
        else:
            item["api_url"] = settings.person_c_api_url
            item["api_key_configured"] = bool(settings.person_c_sync_api_key)
            if check_remote:
                item["remote_health"] = _remote_health(settings.person_c_api_url)
        sources.append(item)
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
        "note": (
            "Sync status only reflects saved outcomes. A previously successful sync is "
            "shown even when the other application is currently offline."
        ),
    }
