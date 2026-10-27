from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from config import settings
from database import to_naive_utc
from models import ElectricityReading

IST = ZoneInfo("Asia/Kolkata")


def _shift_month_start(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    year, month_index = divmod(index, 12)
    return date(year, month_index + 1, 1)


def _month_end(value: date) -> date:
    return date(
        value.year, value.month, calendar.monthrange(value.year, value.month)[1]
    )


def seed_history(client, db, rated: str = "1000.00"):
    socket = client.post(
        "/sockets",
        json={
            "name": "History socket",
            "appliance": "Air conditioner",
            "rated_power_w": rated,
            "location": "Living room",
        },
    ).json()
    today = date.today()
    start_month = _shift_month_start(today.replace(day=1), -7)
    current = datetime.combine(start_month, time.min, tzinfo=IST)
    end = datetime.now(IST).replace(minute=0, second=0, microsecond=0)
    while current <= end:
        db.add(
            ElectricityReading(
                socket_id=socket["id"],
                reading_at=to_naive_utc(current),
                power_w=Decimal("500"),
                source="simulated",
                is_simulated=True,
                quality_flag="ok",
                out_of_order=False,
                notes="Test history",
            )
        )
        current += timedelta(hours=2)
    db.commit()

    bills = []
    current_month = today.replace(day=1)
    for offset in range(6, 0, -1):
        period_start = _shift_month_start(current_month, -offset)
        period_end = _month_end(period_start)
        days = (period_end - period_start).days + 1
        estimated_units = Decimal("500") * Decimal(days * 24) / Decimal("1000")
        actual_units = (estimated_units * Decimal("1.20")).quantize(Decimal("0.01"))
        amount = (actual_units * Decimal("9") + Decimal("100")).quantize(
            Decimal("0.01")
        )
        response = client.post(
            "/bills",
            json={
                "bill_reference": f"TEST-{period_start.strftime('%Y-%m')}",
                "billing_period_start": period_start.isoformat(),
                "billing_period_end": period_end.isoformat(),
                "billed_units": str(actual_units),
                "bill_amount": str(amount),
                "bill_date": period_end.isoformat(),
                "source": "test",
                "notes": "Synthetic test bill",
            },
        )
        assert response.status_code == 201, response.text
        bills.append(response.json())
    return socket, bills


def test_bill_comparison_and_six_month_analysis(client, db):
    _, bills = seed_history(client, db)
    bill = bills[-1]
    response = client.get(f"/bills/compare/{bill['id']}?tolerance_percent=10")
    assert response.status_code == 200, response.text
    body = response.json()
    assert Decimal(body["estimated_units"]) > 0
    assert Decimal(body["unit_deviation"]) > 0
    assert Decimal(body["percentage_deviation"]) > 10
    assert body["exceeds_tolerance"] is True
    assert body["is_estimate"] is True
    assert body["tariff"]["is_verified"] is False
    assert body["six_month_analysis"] is not None
    analysis = body["six_month_analysis"]
    assert analysis["insufficient_history"] is False
    assert len(analysis["historical_months"]) == 6
    assert analysis["analysis_window"]["months_with_readings"] >= 5
    assert analysis["observed_facts"]
    assert analysis["possible_explanations"]
    assert analysis["disclaimer"]
    assert "does not" in analysis["disclaimer"].lower()
    assert "incorrect bill" not in " ".join(analysis["observed_facts"]).lower()
    assert analysis["recurring_estimation_difference"] is True


def test_six_month_endpoint_returns_analysis(client, db):
    _, bills = seed_history(client, db)
    response = client.get(
        f"/analysis/six-months?bill_id={bills[-1]['id']}&tolerance_percent=5"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["bill_reference"] == bills[-1]["bill_reference"]
    assert "observed_facts" in body
    assert "possible_explanations" in body
    assert body["disclaimer"]


def test_tolerance_can_suppress_analysis(client, db):
    _, bills = seed_history(client, db)
    response = client.get(f"/bills/compare/{bills[-1]['id']}?tolerance_percent=100")
    assert response.status_code == 200
    assert response.json()["exceeds_tolerance"] is False
    assert response.json()["six_month_analysis"] is None


def test_comparison_without_readings_is_rejected(client):
    client.post(
        "/sockets",
        json={"name": "Unused socket", "appliance": "Lamp", "rated_power_w": "60"},
    )
    bill = client.post(
        "/bills",
        json={
            "bill_reference": "NO-DATA-1",
            "billing_period_start": "2026-09-01",
            "billing_period_end": "2026-09-30",
            "billed_units": "100",
            "bill_amount": "900",
            "bill_date": "2026-10-01",
        },
    ).json()
    response = client.get(f"/bills/compare/{bill['id']}")
    assert response.status_code == 422
    assert "no usable" in response.json()["detail"].lower()
    assert response.json()["details"]["coverage_pct"] == 0.0


def test_bill_csv_import_and_export(client):
    valid = (
        "bill_reference,billing_period_start,billing_period_end,billed_units,bill_amount,bill_date,source,notes\n"
        "CSV-1,2026-08-01,2026-08-31,210.5,1650.25,2026-09-01,csv,Imported test\n"
    )
    response = client.post(
        "/bills/import/csv",
        files={"file": ("bills.csv", valid, "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["imported"] == 1
    bills = client.get("/bills").json()
    assert bills[0]["bill_reference"] == "CSV-1"

    invalid = (
        "bill_reference,billing_period_start,billing_period_end,billed_units,bill_amount,bill_date\n"
        "CSV-2,2026-09-01,2026-08-01,-4,-10,2026-09-02\n"
    )
    bad = client.post(
        "/bills/import/csv",
        files={"file": ("bills.csv", invalid, "text/csv")},
    )
    assert bad.status_code == 422
    assert len(client.get("/bills").json()) == 1

    exported = client.get("/exports/bill-comparisons.csv")
    assert exported.status_code == 200
    assert "bill_reference" in exported.text


def test_consumption_and_comparison_exports(client, db):
    _, bills = seed_history(client, db)
    client.get(f"/bills/compare/{bills[-1]['id']}")
    consumption = client.get(
        "/exports/consumption.csv?start_date=2026-01-01&end_date=2026-01-31"
    )
    assert consumption.status_code == 200
    assert "date,energy_kwh,coverage_pct" in consumption.text
    comparisons = client.get("/exports/bill-comparisons.csv")
    assert comparisons.status_code == 200
    assert "percentage_deviation" in comparisons.text
    assert "TEST-" in comparisons.text
