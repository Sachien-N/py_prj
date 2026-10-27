from __future__ import annotations

from decimal import Decimal


def _expense(client, amount, day, merchant, category=None):
    payload = {
        "amount": amount,
        "expense_date": f"2026-10-{day:02d}",
        "merchant": merchant,
        "payment_method": "upi",
    }
    if category:
        payload["category"] = category
    response = client.post("/expenses", json=payload)
    assert response.status_code == 201, response.text


def test_budget_usage_remaining_and_exceeded(client):
    _expense(client, "1200.00", 1, "BigBasket groceries")
    _expense(client, "600.00", 2, "Metro card")
    _expense(client, "250.00", 3, "Cafe Coffee Day")

    overall = client.post(
        "/budgets",
        json={"month": "2026-10", "amount": "2000.00", "notes": "Monthly cap"},
    )
    assert overall.status_code == 201, overall.text
    assert overall.json()["scope"] == "overall"

    food = client.post(
        "/budgets",
        json={"month": "2026-10", "amount": "1500.00", "category": "Food"},
    )
    assert food.status_code == 201, food.text

    duplicate = client.post(
        "/budgets",
        json={"month": "2026-10", "amount": "100.00", "category": "Food"},
    )
    assert duplicate.status_code == 409

    overview = client.get("/budgets?month=2026-10").json()
    assert Decimal(overview["total_budget"]) == Decimal("2000.00")
    assert Decimal(overview["total_spent"]) == Decimal("2050.00")
    assert Decimal(overview["remaining"]) == Decimal("-50.00")
    assert overview["exceeded"] is True

    food_budget = next(item for item in overview["budgets"] if item["category"] == "Food")
    assert Decimal(food_budget["spent"]) == Decimal("1450.00")
    assert food_budget["exceeded"] is False

    updated = client.put(
        f"/budgets/{overall.json()['id']}", json={"amount": "3000.00"}
    )
    assert updated.status_code == 200
    assert Decimal(updated.json()["remaining"]) == Decimal("950.00")


def test_budget_requires_valid_month_and_category(client):
    assert (
        client.post("/budgets", json={"month": "2026-13", "amount": "100"}).status_code
        == 422
    )
    assert (
        client.post(
            "/budgets",
            json={"month": "2026-10", "amount": "100", "category": "Nope"},
        ).status_code
        == 422
    )


def test_monthly_report_aggregation(client):
    _expense(client, "500.00", 4, "Swiggy dinner")
    _expense(client, "700.00", 5, "Amazon shoes")
    _expense(client, "200.00", 6, "Netflix subscription")
    report = client.get("/reports/monthly?month=2026-10&months=3")
    assert report.status_code == 200, report.text
    body = report.json()
    assert body["summary"]["transaction_count"] == 3
    assert Decimal(body["summary"]["total_expenses"]) == Decimal("1400.00")
    categories = {item["category"]: item["expense"] for item in body["summary"]["by_category"]}
    assert categories["Food"] == "500.00"
    assert categories["Shopping"] == "700.00"
    assert len(body["monthly_trend"]) == 3
    assert body["daily_trend"][0]["date"] == "2026-10-04"
