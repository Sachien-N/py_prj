from __future__ import annotations

from datetime import date
from decimal import Decimal

from config import settings
from tests.test_bills_analysis import seed_history


def test_electricity_expenses_and_payload(client, db):
    seed_history(client, db)
    # Use the same seven-month horizon as the synthetic history.
    from tests.test_bills_analysis import _shift_month_start

    start = _shift_month_start(date.today().replace(day=1), -7)
    response = client.get(
        f"/expenses/electricity?start_date={start}&end_date={date.today()}"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary"]["records"] > 0
    assert body["summary"]["actual_records"] >= 1
    assert body["summary"]["estimated_records"] >= 1
    for record in body["records"]:
        assert record["source_app"] == "person_c"
        assert record["external_id"].startswith("electricity:")
        assert record["currency"] == "INR"
        assert Decimal(record["expense_amount"]) > 0
        assert "data_coverage_pct" in record

    unauthorized = client.get("/integrations/person-a/payload")
    assert unauthorized.status_code == 401
    payload_response = client.get(
        "/integrations/person-a/payload",
        headers={"X-API-Key": "test-c-key"},
        params={"start_date": start.isoformat(), "end_date": date.today().isoformat()},
    )
    assert payload_response.status_code == 200, payload_response.text
    payload = payload_response.json()
    assert payload["source_app"] == "person_c"
    assert payload["expense_records"]
    assert "test-c-key" not in payload_response.text
    assert payload["summary"]["currency"] == "INR"


def test_integration_sync_failure_preserves_local_data(client, db, monkeypatch):
    socket, bills = seed_history(client, db)
    monkeypatch.setattr(settings, "person_a_api_url", "http://127.0.0.1:9")
    monkeypatch.setattr(settings, "integration_retries", 0)
    response = client.post(
        "/integrations/person-a/sync",
        headers={"X-API-Key": "test-c-key"},
    )
    assert response.status_code == 503
    assert response.json()["details"]["status"] == "failure"
    assert client.get("/sockets").status_code == 200
    assert len(client.get("/bills").json()) == len(bills)
    status = client.get("/integrations/person-a/status").json()
    assert status["status"] == "failure"
    assert status["last_success_at"] is None


def test_demo_seed_is_labelled_simulated(client):
    response = client.post(
        "/demo/seed", json={"months": 2, "force": True}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["simulated"] is True
    assert body["sockets"] == 3
    assert body["bills_created"] >= 1
    sockets = client.get("/sockets").json()
    assert all(item["is_demo"] for item in sockets)
    readings = client.get("/sockets/readings?limit=10").json()
    assert readings
    assert all(item["is_simulated"] for item in readings)
    bills = client.get("/bills").json()
    assert bills
    assert all("SIMULATED" in bill["source"].upper() for bill in bills)


def test_simulate_socket_endpoint(client):
    socket = client.post(
        "/sockets",
        json={"name": "Simulation socket", "appliance": "Fan", "rated_power_w": "75"},
    ).json()
    response = client.post(
        f"/sockets/{socket['id']}/simulate?days=3&interval_minutes=120"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["simulated"] is True
    assert body["created"] > 0
    readings = client.get(f"/sockets/{socket['id']}/readings").json()
    assert readings
    assert all(item["is_simulated"] for item in readings)
