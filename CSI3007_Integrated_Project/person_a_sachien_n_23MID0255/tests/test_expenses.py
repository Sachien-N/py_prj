from __future__ import annotations

from decimal import Decimal


def test_health_and_project_info(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["registration_no"] == "23MID0255"

    info = client.get("/project-info").json()
    assert info["owner"] == "Sachien N"


def test_expense_crud_auto_categorization_and_override(client, expense_payload):
    created = client.post("/expenses", json=expense_payload)
    assert created.status_code == 201, created.text
    expense = created.json()
    assert expense["category"] == "Food"
    assert expense["amount"] == "250.50"
    assert expense["source_app"] == "local"
    expense_id = expense["id"]

    fetched = client.get(f"/expenses/{expense_id}")
    assert fetched.status_code == 200
    assert fetched.json()["merchant"] == "Zomato lunch"

    updated = client.put(
        f"/expenses/{expense_id}",
        json={
            "merchant": "Uber airport ride",
            "category": "Transport",
            "amount": "400.00",
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["category"] == "Transport"
    assert updated.json()["amount"] == "400.00"

    invalid_category = client.put(
        f"/expenses/{expense_id}", json={"category": "Not a category"}
    )
    assert invalid_category.status_code == 422

    deleted = client.delete(f"/expenses/{expense_id}")
    assert deleted.status_code == 204
    assert client.get(f"/expenses/{expense_id}").status_code == 404


def test_invalid_amounts_and_dates_are_rejected(client, expense_payload):
    bad_amount = {**expense_payload, "amount": "-5"}
    assert client.post("/expenses", json=bad_amount).status_code == 422

    bad_date = {**expense_payload, "expense_date": "not-a-date"}
    assert client.post("/expenses", json=bad_date).status_code == 422

    bad_type = {**expense_payload, "transaction_type": "transfer"}
    assert client.post("/expenses", json=bad_type).status_code == 422


def test_refunds_reduce_net_spending_and_are_capped(client):
    original = client.post(
        "/expenses",
        json={
            "amount": "1000.00",
            "expense_date": "2026-10-01",
            "merchant": "Apollo pharmacy",
            "payment_method": "card",
            "transaction_type": "expense",
        },
    ).json()
    assert original["category"] == "Healthcare"

    partial = client.post(
        "/expenses",
        json={
            "amount": "250.00",
            "expense_date": "2026-10-02",
            "merchant": "Refund from Apollo",
            "payment_method": "card",
            "transaction_type": "refund",
            "refund_of_expense_id": original["id"],
        },
    )
    assert partial.status_code == 201, partial.text
    assert partial.json()["category"] == "Healthcare"

    too_much = client.post(
        "/expenses",
        json={
            "amount": "800.00",
            "expense_date": "2026-10-03",
            "merchant": "Duplicate refund",
            "payment_method": "card",
            "transaction_type": "refund",
            "refund_of_expense_id": original["id"],
        },
    )
    assert too_much.status_code == 422

    summary = client.get(
        "/expenses/summary?start_date=2026-10-01&end_date=2026-10-31"
    ).json()
    assert Decimal(summary["total_expenses"]) == Decimal("1000.00")
    assert Decimal(summary["total_refunds"]) == Decimal("250.00")
    assert Decimal(summary["net_spending"]) == Decimal("750.00")


def test_search_and_date_filters(client):
    for payload in [
        {
            "amount": "100.00",
            "expense_date": "2026-09-01",
            "merchant": "Metro card",
            "payment_method": "upi",
        },
        {
            "amount": "300.00",
            "expense_date": "2026-10-01",
            "merchant": "Amazon headphones",
            "payment_method": "card",
        },
    ]:
        assert client.post("/expenses", json=payload).status_code == 201

    october = client.get(
        "/expenses?start_date=2026-10-01&end_date=2026-10-31"
    ).json()
    assert len(october) == 1
    assert october[0]["category"] == "Shopping"

    searched = client.get("/expenses?search=metro").json()
    assert len(searched) == 1
    assert searched[0]["merchant"] == "Metro card"
