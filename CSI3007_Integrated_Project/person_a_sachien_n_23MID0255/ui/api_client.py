"""HTTP-only client used by the Streamlit dashboard.

The dashboard never imports SQLAlchemy models and never opens the SQLite file.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import requests

from config import settings


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class ExpenseApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 12.0):
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, **kwargs) -> Any:
        timeout = kwargs.pop("timeout", self.timeout)
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                timeout=timeout,
                **kwargs,
            )
        except requests.Timeout:
            raise ApiError("The expense API timed out. Is the API server running?")
        except requests.ConnectionError:
            raise ApiError(
                "Cannot reach the expense API at "
                f"{self.base_url}. Start it with: python -m uvicorn api:app --port 8001"
            )
        except requests.RequestException:
            raise ApiError("The expense API request failed safely.")
        if response.status_code >= 400:
            detail = "Request failed"
            details = None
            try:
                body = response.json()
                if isinstance(body.get("detail"), str):
                    detail = body["detail"]
                elif body.get("detail"):
                    detail = str(body["detail"])
                details = body.get("details")
            except ValueError:
                detail = f"API returned HTTP {response.status_code}"
            raise ApiError(detail, response.status_code, details)
        if response.status_code == 204 or not response.content:
            return None
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return response

    def health(self) -> dict:
        return self._request("GET", "/health")

    def project_info(self) -> dict:
        return self._request("GET", "/project-info")

    def categories(self, include_inactive: bool = False) -> list[dict]:
        return self._request(
            "GET", "/categories", params={"include_inactive": include_inactive}
        )

    def create_category(self, payload: dict) -> dict:
        return self._request("POST", "/categories", json=payload)

    def update_category(self, category_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/categories/{category_id}", json=payload)

    def delete_category(self, category_id: int) -> None:
        self._request("DELETE", f"/categories/{category_id}")

    def expenses(self, **filters) -> list[dict]:
        params = {key: value for key, value in filters.items() if value not in (None, "")}
        for key, value in list(params.items()):
            if isinstance(value, date):
                params[key] = value.isoformat()
        return self._request("GET", "/expenses", params=params)

    def expense(self, expense_id: int) -> dict:
        return self._request("GET", f"/expenses/{expense_id}")

    def create_expense(self, payload: dict) -> dict:
        return self._request("POST", "/expenses", json=payload)

    def update_expense(self, expense_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/expenses/{expense_id}", json=payload)

    def delete_expense(self, expense_id: int) -> None:
        self._request("DELETE", f"/expenses/{expense_id}")

    def summary(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> dict:
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()
        return self._request("GET", "/expenses/summary", params=params)

    def budget_overview(self, month: str) -> dict:
        return self._request("GET", "/budgets", params={"month": month})

    def create_budget(self, payload: dict) -> dict:
        return self._request("POST", "/budgets", json=payload)

    def update_budget(self, budget_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/budgets/{budget_id}", json=payload)

    def delete_budget(self, budget_id: int) -> None:
        self._request("DELETE", f"/budgets/{budget_id}")

    def monthly_report(self, month: str, months: int = 6) -> dict:
        return self._request(
            "GET", "/reports/monthly", params={"month": month, "months": months}
        )

    def integration_status(self, check_remote: bool = False) -> dict:
        return self._request(
            "GET",
            "/integrations/status",
            params={"check_remote": str(check_remote).lower()},
            timeout=10,
        )

    def sync_subscriptions(self) -> dict:
        return self._request(
            "POST", "/integrations/subscriptions/sync", timeout=30
        )

    def sync_electricity(self) -> dict:
        return self._request("POST", "/integrations/electricity/sync", timeout=30)

    def import_csv(self, filename: str, content: bytes) -> dict:
        return self._request(
            "POST",
            "/expenses/import/csv",
            files={"file": (filename, content, "text/csv")},
        )

    def export_csv(self, **filters) -> bytes:
        params = {key: value for key, value in filters.items() if value not in (None, "")}
        for key, value in list(params.items()):
            if isinstance(value, date):
                params[key] = value.isoformat()
        response = self._request("GET", "/expenses/export.csv", params=params)
        return response.content


client = ExpenseApiClient()
