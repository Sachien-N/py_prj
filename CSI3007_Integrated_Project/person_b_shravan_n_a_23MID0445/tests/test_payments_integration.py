from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from config import settings


def _subscription(**overrides):
    payload = {
        "service_name": "Adobe Creative Cloud",
        "category": "Software",
        "amount": "500.00",
        "currency": "INR",
        "billing_cycle": "monthly",
        "start_date": (date.today() - timedelta(days=60)).isoformat(),
        "payment_method": "card",
        "status": "active",
        "reminder_days_before": 7,
    }
    payload.update(overrides)
    return payload


def _create(client):
    response = client.post("/subscriptions", json=_subscription())
    assert response.status_code == 201, response.text
    return response.json()


def test_payment_is_idempotent_and_appears_in_history(client):
    subscription = _create(client)
    today = date.today()
    payload = {
        "subscription_id": subscription["id"],
        "amount": "480.00",
        "paid_on": today.isoformat(),
        "billing_period": today.strftime("%Y-%m"),
        "payment_method": "card",
        "reference": "CARD-123",
        "idempotency_key": "idem-payment-001",
    }
    first = client.post("/subscriptions/payments", json=payload)
    assert first.status_code == 200, first.text
    assert first.json()["created"] is True
    second = client.post("/subscriptions/payments", json=payload)
    assert second.status_code == 200
    assert second.json()["deduplicated"] is True
    assert second.json()["id"] == first.json()["id"]
    history = client.get("/subscriptions/payments").json()
    assert len(history) == 1
    assert history[0]["amount"] == "480.00"

    summary = client.get("/subscriptions/summary").json()
    assert Decimal(summary["actual_payments_this_month"]) == Decimal("480.00")
    assert Decimal(summary["expected_monthly_recurring"]) == Decimal("500.00")


def test_payment_rejects_future_currency_mismatch_and_duplicate_period(client):
    subscription = _create(client)
    today = date.today()
    future = client.post(
        "/subscriptions/payments",
        json={
            "subscription_id": subscription["id"],
            "amount": "480.00",
            "paid_on": (today + timedelta(days=1)).isoformat(),
            "idempotency_key": "future-key-1",
        },
    )
    assert future.status_code == 422
    mismatch = client.post(
        "/subscriptions/payments",
        json={
            "subscription_id": subscription["id"],
            "amount": "480.00",
            "paid_on": today.isoformat(),
            "currency": "USD",
            "idempotency_key": "currency-key-1",
        },
    )
    assert mismatch.status_code == 422

    period = today.strftime("%Y-%m")
    first = client.post(
        "/subscriptions/payments",
        json={
            "subscription_id": subscription["id"],
            "amount": "480.00",
            "paid_on": today.isoformat(),
            "billing_period": period,
            "idempotency_key": "period-key-1",
        },
    )
    assert first.status_code == 200
    second = client.post(
        "/subscriptions/payments",
        json={
            "subscription_id": subscription["id"],
            "amount": "450.00",
            "paid_on": today.isoformat(),
            "billing_period": period,
            "idempotency_key": "period-key-2",
        },
    )
    assert second.status_code == 200
    assert second.json()["deduplicated"] is True
    assert second.json()["id"] == first.json()["id"]


def test_payload_generation_is_authenticated_and_secret_free(client):
    subscription = _create(client)
    today = date.today()
    client.post(
        "/subscriptions/payments",
        json={
            "subscription_id": subscription["id"],
            "amount": "480.00",
            "paid_on": today.isoformat(),
            "billing_period": today.strftime("%Y-%m"),
            "idempotency_key": "payload-key-1",
        },
    )
    unauthorized = client.get("/integrations/person-a/payload")
    assert unauthorized.status_code == 401
    response = client.get(
        "/integrations/person-a/payload",
        headers={"X-API-Key": "test-a-key"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["source_app"] == "person_b"
    assert len(payload["expense_records"]) == 1
    record = payload["expense_records"][0]
    assert record["external_id"].startswith("sub:")
    assert record["is_estimate"] is False
    assert record["amount"] == "480.00"
    assert "test-a-key" not in response.text
    assert "password" not in response.text.lower()


def test_sync_failure_preserves_local_data(client, monkeypatch):
    subscription = _create(client)
    monkeypatch.setattr(settings, "person_a_api_url", "http://127.0.0.1:9")
    monkeypatch.setattr(settings, "integration_retries", 0)
    response = client.post(
        "/integrations/person-a/sync",
        headers={"X-API-Key": "test-a-key"},
    )
    assert response.status_code == 503
    assert response.json()["details"]["status"] == "failure"
    assert len(client.get("/subscriptions").json()) == 1
    status = client.get("/integrations/person-a/status").json()
    assert status["status"] == "failure"
    assert status["last_success_at"] is None
    assert client.get(f"/subscriptions/{subscription['id']}").status_code == 200
