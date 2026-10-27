from __future__ import annotations


def test_csv_import_validates_then_imports_atomically(client):
    invalid = (
        "date,amount,merchant,category,payment_method,description,transaction_type,currency\n"
        "2026-10-01,100.00,Metro card,Transport,upi,,\n"
        "2026-10-02,not-a-number,Bad row,Food,card,,\n"
    )
    response = client.post(
        "/expenses/import/csv",
        files={"file": ("expenses.csv", invalid, "text/csv")},
    )
    assert response.status_code == 422
    assert response.json()["details"]["imported"] == 0
    assert client.get("/expenses").json() == []

    valid = (
        "date,amount,merchant,category,payment_method,description,transaction_type,currency\n"
        "2026-10-01,100.00,Metro card,Transport,upi,Commute,expense,INR\n"
        "2026-10-02,450.00,Apollo pharmacy,,card,Medicines,expense,INR\n"
    )
    response = client.post(
        "/expenses/import/csv",
        files={"file": ("expenses.csv", valid, "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["imported"] == 2
    items = client.get("/expenses").json()
    assert len(items) == 2
    categories = {item["merchant"]: item["category"] for item in items}
    assert categories["Metro card"] == "Transport"
    assert categories["Apollo pharmacy"] == "Healthcare"


def test_csv_missing_columns_and_wrong_type_are_rejected(client):
    missing = "date,amount\n2026-10-01,10\n"
    response = client.post(
        "/expenses/import/csv",
        files={"file": ("bad.csv", missing, "text/csv")},
    )
    assert response.status_code == 422
    assert "missing required columns" in response.json()["detail"].lower()

    wrong_type = client.post(
        "/expenses/import/csv",
        files={"file": ("bad.txt", b"not csv", "text/plain")},
    )
    assert wrong_type.status_code == 415


def test_csv_export_has_expected_columns(client, expense_payload):
    assert client.post("/expenses", json=expense_payload).status_code == 201
    response = client.get("/expenses/export.csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    lines = response.text.strip().splitlines()
    assert lines[0].startswith("id,date,amount,currency,merchant")
    assert "Zomato lunch" in response.text
