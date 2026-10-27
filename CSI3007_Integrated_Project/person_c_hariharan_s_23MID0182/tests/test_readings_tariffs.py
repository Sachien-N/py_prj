from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from services.tariff_service import calculate_estimate

IST = ZoneInfo("Asia/Kolkata")


def _socket(client, name="Living room AC", rated="1000.00"):
    response = client.post(
        "/sockets",
        json={
            "name": name,
            "appliance": "Air conditioner",
            "rated_power_w": rated,
            "location": "Living room",
            "adapter_type": "manual",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _reading(client, socket_id, when: datetime, power: str, source="manual"):
    response = client.post(
        "/sockets/readings",
        json={
            "socket_id": socket_id,
            "reading_at": when.isoformat(),
            "power_w": power,
            "source": source,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_health_and_socket_crud(client):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["owner"] == "HARIHARAN S"
    assert health.json()["registration_no"] == "23MID0182"

    socket = _socket(client)
    duplicate = client.post(
        "/sockets",
        json={
            "name": "LIVING ROOM AC",
            "appliance": "AC",
            "rated_power_w": "1000",
        },
    )
    assert duplicate.status_code == 409
    updated = client.put(
        f"/sockets/{socket['id']}", json={"rated_power_w": "1200", "location": "Hall"}
    )
    assert updated.status_code == 200
    assert updated.json()["rated_power_w"] == "1200.00"
    assert client.get("/sockets").json()[0]["name"] == "Living room AC"
    assert client.delete(f"/sockets/{socket['id']}").status_code == 204
    assert client.get(f"/sockets/{socket['id']}").status_code == 404


def test_daily_energy_uses_power_times_duration(client):
    socket = _socket(client)
    day = date(2026, 9, 1)
    _reading(client, socket["id"], datetime(2026, 9, 1, 0, 0, tzinfo=IST), "1000")
    _reading(client, socket["id"], datetime(2026, 9, 1, 1, 0, tzinfo=IST), "500")
    _reading(client, socket["id"], datetime(2026, 9, 1, 2, 0, tzinfo=IST), "0")

    response = client.get(
        f"/consumption/daily?start_date={day}&end_date={day}"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_energy_kwh"] == "1.500"
    assert body["days"][0]["energy_kwh"] == "1.500"
    assert body["days"][0]["coverage_pct"] == pytest.approx(8.33, abs=0.01)
    assert body["gaps"] == []

    monthly = client.get(
        "/consumption/monthly?start_date=2026-09-01&end_date=2026-09-30"
    ).json()
    assert monthly["months"][0]["energy_kwh"] == "1.500"
    by_socket = client.get(
        "/consumption/by-socket?start_date=2026-09-01&end_date=2026-09-30"
    ).json()
    assert by_socket["sockets"][0]["energy_kwh"] == "1.500"

    estimate = client.get(
        "/consumption/estimate?start_date=2026-09-01&end_date=2026-09-01"
    ).json()
    assert Decimal(estimate["estimated_cost"]) > 0
    assert estimate["tariff"]["is_verified"] is False
    costs = client.get(
        "/consumption/monthly-costs?start_date=2026-09-01&end_date=2026-09-30"
    ).json()
    assert costs["months"][0]["estimated_cost"] == estimate["estimated_cost"]


def test_reading_validation_duplicate_and_out_of_order(client):
    socket = _socket(client)
    later = datetime(2026, 9, 2, 3, 0, tzinfo=IST)
    earlier = datetime(2026, 9, 2, 1, 0, tzinfo=IST)
    _reading(client, socket["id"], later, "400")
    out_of_order = _reading(client, socket["id"], earlier, "300")
    assert out_of_order["out_of_order"] is True

    duplicate = client.post(
        "/sockets/readings",
        json={
            "socket_id": socket["id"],
            "reading_at": later.isoformat(),
            "power_w": "200",
        },
    )
    assert duplicate.status_code == 409

    naive = client.post(
        "/sockets/readings",
        json={
            "socket_id": socket["id"],
            "reading_at": "2026-09-02T04:00:00",
            "power_w": "200",
        },
    )
    assert naive.status_code == 422
    future = datetime.now(IST) + timedelta(days=1)
    future_response = client.post(
        "/sockets/readings",
        json={
            "socket_id": socket["id"],
            "reading_at": future.isoformat(),
            "power_w": "200",
        },
    )
    assert future_response.status_code == 422

    above_rated = _reading(
        client, socket["id"], datetime(2026, 9, 2, 5, 0, tzinfo=IST), "1500"
    )
    assert above_rated["quality_flag"] == "above_rated_power"


def test_long_gap_is_excluded_and_reported(client):
    socket = _socket(client)
    _reading(client, socket["id"], datetime(2026, 9, 3, 0, 0, tzinfo=IST), "1000")
    _reading(client, socket["id"], datetime(2026, 9, 3, 6, 0, tzinfo=IST), "1000")
    body = client.get(
        "/consumption/daily?start_date=2026-09-03&end_date=2026-09-03"
    ).json()
    assert body["total_energy_kwh"] == "0.000"
    assert body["days"][0]["energy_kwh"] is None
    assert len(body["gaps"]) == 1
    assert any("gap" in warning.lower() for warning in body["warnings"])


def test_tariff_engine_progressive_slabs_and_components(db):
    estimate = calculate_estimate(
        db, units=Decimal("250"), on_date=date(2026, 9, 30), category="domestic"
    )
    assert estimate["energy_charge"] == "1450.00"
    assert estimate["component_total"] == "122.50"
    assert estimate["total_cost"] == "1572.50"
    assert estimate["tariff"]["is_verified"] is False
    assert "DEMO" in estimate["tariff"]["name"]
    assert estimate["is_estimate"] is True
    assert len(estimate["slab_breakdown"]) == 3
    assert estimate["slab_breakdown"][2]["units_in_slab"] == "50.00"


def test_tariff_validation_and_listing(client):
    tariffs = client.get("/tariffs").json()
    assert len(tariffs) == 1
    assert tariffs[0]["is_verified"] is False
    assert "not official" in tariffs[0]["name"].lower()

    missing_key = client.post("/tariffs", json={"name": "bad"})
    assert missing_key.status_code == 422
    gap = client.post(
        "/tariffs",
        json={
            "name": "Gap tariff",
            "category": "domestic",
            "effective_from": "2026-01-01",
            "source": "Test",
            "slabs": [
                {"from_units": "0", "to_units": "100", "rate_per_unit": "4"},
                {"from_units": "150", "to_units": None, "rate_per_unit": "7"},
            ],
        },
    )
    assert gap.status_code == 422

    created = client.post(
        "/tariffs",
        json={
            "name": "Verified test tariff",
            "category": "domestic",
            "effective_from": "2027-01-01",
            "source": "Test tariff order",
            "is_verified": True,
            "slabs": [
                {"from_units": "0", "to_units": "100", "rate_per_unit": "5"},
                {"from_units": "100", "to_units": None, "rate_per_unit": "8"},
            ],
            "components": [
                {"name": "Fixed", "charge_type": "fixed_monthly", "amount": "25"}
            ],
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["is_verified"] is True
