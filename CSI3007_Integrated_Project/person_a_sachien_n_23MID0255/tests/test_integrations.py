from __future__ import annotations

from decimal import Decimal

from config import settings


def _subscription_payload(external_id="sub:1:2026-10"):
    return {
        "source_app": "person_b",
        "generated_at": "2026-10-20T10:00:00",
        "billing_period": "2026-10",
        "summary": {"active_subscriptions": 1},
        "expense_records": [
            {
                "source_app": "person_b",
                "external_id": external_id,
                "subscription_id": 1,
                "service_name": "Netflix",
                "category": "Entertainment",
                "amount": "499.00",
                "currency": "INR",
                "billing_period": "2026-10",
                "billing_date": "2026-10-15",
                "record_updated_at": "2026-10-20T10:00:00",
                "is_estimate": True,
                "description": "Expected monthly subscription cost",
            }
        ],
    }


def _electricity_payload():
    return {
        "source_app": "person_c",
        "generated_at": "2026-10-20T10:05:00",
        "summary": {"months": 1},
        "expense_records": [
            {
                "source_app": "person_c",
                "external_id": "electricity:2026-10",
                "period": "2026-10",
                "billing_date": "2026-10-31",
                "expense_amount": "845.50",
                "currency": "INR",
                "units": "210.5",
                "is_estimate": False,
                "description": "Actual TNEB bill for 2026-10",
                "record_updated_at": "2026-10-20T10:05:00",
                "data_coverage_pct": "75.0",
            }
        ],
    }


def test_subscription_sync_is_authenticated_and_idempotent(client):
    unauthorized = client.post(
        "/integrations/subscriptions/sync", json=_subscription_payload()
    )
    assert unauthorized.status_code == 401

    first = client.post(
        "/integrations/subscriptions/sync",
        json=_subscription_payload(),
        headers={"X-API-Key": "test-b-key"},
    )
    assert first.status_code == 200, first.text
    assert first.json()["records_imported"] == 1

    second = client.post(
        "/integrations/subscriptions/sync",
        json=_subscription_payload(),
        headers={"X-API-Key": "test-b-key"},
    )
    assert second.status_code == 200
    assert second.json()["records_imported"] == 0
    assert second.json()["records_updated"] == 1

    imported = client.get("/expenses?source_app=person_b").json()
    assert len(imported) == 1
    assert imported[0]["external_id"] == "sub:1:2026-10"
    assert imported[0]["is_estimated"] is True
    assert imported[0]["amount"] == "499.00"

    status = client.get("/integrations/status").json()
    b_status = next(item for item in status["sources"] if item["source"] == "person_b")
    assert b_status["status"] == "success"
    assert b_status["items_received"] == 1


def test_electricity_sync_and_wrong_key(client):
    wrong_key = client.post(
        "/integrations/electricity/sync",
        json=_electricity_payload(),
        headers={"X-API-Key": "test-b-key"},
    )
    assert wrong_key.status_code == 401

    response = client.post(
        "/integrations/electricity/sync",
        json=_electricity_payload(),
        headers={"X-API-Key": "test-c-key"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["records_imported"] == 1
    expense = client.get("/expenses?source_app=person_c").json()[0]
    assert expense["category"] == "Utilities"
    assert expense["amount"] == "845.50"
    assert expense["is_estimated"] is False


def test_invalid_external_payload_is_rejected(client):
    invalid = _subscription_payload()
    invalid["expense_records"][0]["amount"] = "-1"
    response = client.post(
        "/integrations/subscriptions/sync",
        json=invalid,
        headers={"X-API-Key": "test-b-key"},
    )
    assert response.status_code == 422
    assert client.get("/expenses").json() == []


def test_unavailable_remote_pull_records_failure_without_fabricating(
    client, monkeypatch
):
    monkeypatch.setattr(settings, "person_b_api_url", "http://127.0.0.1:9")
    monkeypatch.setattr(settings, "integration_retries", 0)
    response = client.post(
        "/integrations/subscriptions/sync",
        headers={"X-API-Key": "test-b-key"},
    )
    assert response.status_code == 503
    assert client.get("/expenses").json() == []
    status = client.get("/integrations/status").json()
    b_status = next(item for item in status["sources"] if item["source"] == "person_b")
    assert b_status["status"] == "failure"
    assert b_status["last_success_at"] is None


def test_duplicate_external_id_updates_same_row(client):
    payload = _subscription_payload()
    headers = {"X-API-Key": "test-b-key"}
    assert client.post(
        "/integrations/subscriptions/sync", json=payload, headers=headers
    ).status_code == 200
    payload["expense_records"][0]["amount"] = "549.00"
    assert client.post(
        "/integrations/subscriptions/sync", json=payload, headers=headers
    ).status_code == 200
    items = client.get("/expenses?source_app=person_b").json()
    assert len(items) == 1
    assert Decimal(items[0]["amount"]) == Decimal("549.00")
