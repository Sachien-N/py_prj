from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal


def _subscription(**overrides):
    payload = {
        "service_name": "Netflix",
        "category": "Entertainment",
        "amount": "500.00",
        "currency": "INR",
        "billing_cycle": "monthly",
        "start_date": "2025-01-01",
        "payment_method": "card",
        "status": "active",
        "notes": "Family plan",
        "reminder_days_before": 7,
    }
    payload.update(overrides)
    return payload


def test_create_health_and_owner(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["owner"] == "Shravan N A"
    assert health.json()["registration_no"] == "23MID0445"


def test_create_subscription_and_projections(client):
    response = client.post("/subscriptions", json=_subscription())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["service_name"] == "Netflix"
    assert body["monthly_equivalent"] == "500.00"
    assert body["yearly_equivalent"] == "6000.00"
    assert body["next_renewal_date"] >= body["start_date"]
    assert body["status"] == "active"

    weekly = client.post(
        "/subscriptions", json=_subscription(service_name="Weekly gym", amount="100.00", billing_cycle="weekly")
    )
    assert weekly.status_code == 201
    assert weekly.json()["monthly_equivalent"] == "433.33"

    custom = client.post(
        "/subscriptions",
        json=_subscription(
            service_name="Every 30 days",
            amount="100.00",
            billing_cycle="custom",
            custom_interval_days=30,
        ),
    )
    assert custom.status_code == 201
    assert custom.json()["monthly_equivalent"] == "101.39"


def test_billing_cycle_validation(client):
    missing_days = client.post(
        "/subscriptions",
        json=_subscription(billing_cycle="custom", custom_interval_days=None),
    )
    assert missing_days.status_code == 422
    invalid_date = client.post(
        "/subscriptions",
        json=_subscription(start_date="2026-02-01", next_renewal_date="2026-01-01"),
    )
    assert invalid_date.status_code == 422
    invalid_amount = client.post("/subscriptions", json=_subscription(amount="0"))
    assert invalid_amount.status_code == 422


def test_update_status_search_and_delete(client):
    created = client.post("/subscriptions", json=_subscription()).json()
    subscription_id = created["id"]
    updated = client.put(
        f"/subscriptions/{subscription_id}",
        json={"status": "paused", "amount": "550.00", "notes": "Paused for now"},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "paused"
    assert updated.json()["amount"] == "550.00"

    found = client.get("/subscriptions?search=paused").json()
    assert len(found) == 1
    status_filter = client.get("/subscriptions?status=active").json()
    assert status_filter == []

    deleted = client.delete(f"/subscriptions/{subscription_id}")
    assert deleted.status_code == 204
    assert client.get(f"/subscriptions/{subscription_id}").status_code == 404


def test_upcoming_overdue_and_reminders(client):
    today = date.today()
    soon = client.post(
        "/subscriptions",
        json=_subscription(
            service_name="Spotify",
            category="Music",
            start_date=(today - timedelta(days=40)).isoformat(),
            next_renewal_date=(today + timedelta(days=3)).isoformat(),
            reminder_days_before=7,
        ),
    )
    assert soon.status_code == 201, soon.text
    overdue = client.post(
        "/subscriptions",
        json=_subscription(
            service_name="Old magazine",
            start_date=(today - timedelta(days=60)).isoformat(),
            next_renewal_date=(today - timedelta(days=2)).isoformat(),
            reminder_days_before=7,
        ),
    )
    assert overdue.status_code == 201
    paused = client.post(
        "/subscriptions",
        json=_subscription(
            service_name="Paused app",
            status="paused",
            start_date=(today - timedelta(days=20)).isoformat(),
            next_renewal_date=(today + timedelta(days=2)).isoformat(),
        ),
    )
    assert paused.status_code == 201

    upcoming = client.get("/subscriptions/upcoming?days=7").json()
    assert upcoming["counts"]["upcoming"] == 1
    assert upcoming["counts"]["overdue"] == 1
    assert upcoming["overdue_records"][0]["service_name"] == "Old magazine"

    refresh = client.post("/subscriptions/reminders/refresh").json()
    assert refresh["created"] >= 2
    reminders = client.get("/subscriptions/reminders").json()
    assert len(reminders) >= 2
    dismissed = client.post(
        f"/subscriptions/reminders/{reminders[0]['id']}/dismiss"
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["status"] == "dismissed"


def test_summary_and_csv_export(client):
    client.post("/subscriptions", json=_subscription())
    client.post(
        "/subscriptions",
        json=_subscription(service_name="Paused", status="paused", amount="200.00"),
    )
    summary = client.get("/subscriptions/summary").json()
    assert summary["active_subscriptions"] == 1
    assert Decimal(summary["expected_monthly_recurring"]) == Decimal("500.00")
    assert Decimal(summary["yearly_projection"]) == Decimal("6000.00")
    assert summary["status_counts"]["paused"] == 1

    exported = client.get("/subscriptions/export.csv")
    assert exported.status_code == 200
    assert "service_name" in exported.text
    assert "Netflix" in exported.text


def test_advance_renewal(client):
    today = date.today()
    created = client.post(
        "/subscriptions",
        json=_subscription(
            start_date=(today - timedelta(days=30)).isoformat(),
            next_renewal_date=(today + timedelta(days=5)).isoformat(),
        ),
    ).json()
    advanced = client.post(
        f"/subscriptions/{created['id']}/advance-renewal"
    )
    assert advanced.status_code == 200
    assert advanced.json()["next_renewal_date"] > created["next_renewal_date"]
