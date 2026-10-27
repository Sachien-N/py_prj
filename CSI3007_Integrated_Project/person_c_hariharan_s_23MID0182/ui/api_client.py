"""HTTP client for Person C's dashboard."""

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


class ElectricityApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 20.0):
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.timeout = timeout

    @property
    def integration_headers(self) -> dict:
        return {"X-API-Key": settings.person_a_sync_api_key}

    def _request(self, method: str, path: str, **kwargs) -> Any:
        timeout = kwargs.pop("timeout", self.timeout)
        try:
            response = requests.request(
                method, f"{self.base_url}{path}", timeout=timeout, **kwargs
            )
        except requests.Timeout:
            raise ApiError(
                "The electricity API timed out. It may still be calculating readings."
            )
        except requests.ConnectionError:
            raise ApiError(
                "Cannot reach the electricity API at "
                f"{self.base_url}. Start it with: python -m uvicorn api:app --port 8003"
            )
        except requests.RequestException:
            raise ApiError("The electricity API request failed safely.")
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

    def _params(self, **values) -> dict:
        result = {}
        for key, value in values.items():
            if value in (None, ""):
                continue
            if isinstance(value, date):
                result[key] = value.isoformat()
            elif isinstance(value, bool):
                result[key] = str(value).lower()
            else:
                result[key] = value
        return result

    def health(self) -> dict:
        return self._request("GET", "/health")

    def sockets(self) -> list[dict]:
        return self._request("GET", "/sockets")

    def create_socket(self, payload: dict) -> dict:
        return self._request("POST", "/sockets", json=payload)

    def update_socket(self, socket_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/sockets/{socket_id}", json=payload)

    def delete_socket(self, socket_id: int) -> None:
        self._request("DELETE", f"/sockets/{socket_id}")

    def readings(self, socket_id: int | None = None, limit: int = 500) -> list[dict]:
        return self._request(
            "GET", "/sockets/readings", params=self._params(socket_id=socket_id, limit=limit)
        )

    def create_reading(self, payload: dict) -> dict:
        return self._request("POST", "/sockets/readings", json=payload)

    def delete_reading(self, reading_id: int) -> None:
        self._request("DELETE", f"/sockets/readings/{reading_id}")

    def simulate(self, socket_id: int, days: int, interval_minutes: int) -> dict:
        return self._request(
            "POST",
            f"/sockets/{socket_id}/simulate",
            params={"days": days, "interval_minutes": interval_minutes},
            timeout=60,
        )

    def daily(self, start_date: date, end_date: date, socket_id: int | None = None) -> dict:
        return self._request(
            "GET",
            "/consumption/daily",
            params=self._params(
                start_date=start_date, end_date=end_date, socket_id=socket_id
            ),
        )

    def monthly(self, start_date: date, end_date: date, socket_id: int | None = None) -> dict:
        return self._request(
            "GET",
            "/consumption/monthly",
            params=self._params(
                start_date=start_date, end_date=end_date, socket_id=socket_id
            ),
        )

    def by_socket(self, start_date: date, end_date: date) -> dict:
        return self._request(
            "GET",
            "/consumption/by-socket",
            params=self._params(start_date=start_date, end_date=end_date),
        )

    def period_estimate(self, start_date: date, end_date: date) -> dict:
        return self._request(
            "GET",
            "/consumption/estimate",
            params=self._params(start_date=start_date, end_date=end_date),
        )

    def monthly_costs(self, start_date: date, end_date: date) -> dict:
        return self._request(
            "GET",
            "/consumption/monthly-costs",
            params=self._params(start_date=start_date, end_date=end_date),
        )

    def tariffs(self, include_inactive: bool = True) -> list[dict]:
        return self._request(
            "GET", "/tariffs", params={"include_inactive": str(include_inactive).lower()}
        )

    def create_tariff(self, payload: dict) -> dict:
        return self._request("POST", "/tariffs", json=payload)

    def update_tariff(self, tariff_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/tariffs/{tariff_id}", json=payload)

    def bills(self, start_date: date | None = None, end_date: date | None = None) -> list[dict]:
        return self._request(
            "GET", "/bills", params=self._params(start_date=start_date, end_date=end_date)
        )

    def create_bill(self, payload: dict) -> dict:
        return self._request("POST", "/bills", json=payload)

    def delete_bill(self, bill_id: int) -> None:
        self._request("DELETE", f"/bills/{bill_id}")

    def compare(self, bill_id: int, tolerance: float | None = None, tariff_id=None) -> dict:
        return self._request(
            "GET",
            f"/bills/compare/{bill_id}",
            params=self._params(tolerance_percent=tolerance, tariff_id=tariff_id),
        )

    def analysis(self, bill_id: int, tolerance: float | None = None) -> dict:
        return self._request(
            "GET",
            "/analysis/six-months",
            params=self._params(bill_id=bill_id, tolerance_percent=tolerance),
        )

    def import_bills(self, filename: str, content: bytes) -> dict:
        return self._request(
            "POST",
            "/bills/import/csv",
            files={"file": (filename, content, "text/csv")},
        )

    def electricity_expenses(self, start_date: date, end_date: date) -> dict:
        return self._request(
            "GET",
            "/expenses/electricity",
            params=self._params(start_date=start_date, end_date=end_date),
        )

    def demo_seed(self, months: int = 6, force: bool = False) -> dict:
        return self._request(
            "POST",
            "/demo/seed",
            json={"months": months, "force": force},
            timeout=120,
        )

    def integration_status(self, check_remote: bool = False) -> dict:
        return self._request(
            "GET",
            "/integrations/person-a/status",
            params={"check_remote": str(check_remote).lower()},
            timeout=10,
        )

    def integration_payload(self, start_date: date, end_date: date) -> dict:
        return self._request(
            "GET",
            "/integrations/person-a/payload",
            headers=self.integration_headers,
            params=self._params(start_date=start_date, end_date=end_date),
        )

    def sync_person_a(self, start_date: date, end_date: date) -> dict:
        return self._request(
            "POST",
            "/integrations/person-a/sync",
            headers=self.integration_headers,
            params=self._params(start_date=start_date, end_date=end_date),
            timeout=60,
        )

    def export_consumption(self, start_date: date, end_date: date) -> bytes:
        response = self._request(
            "GET",
            "/exports/consumption.csv",
            params=self._params(start_date=start_date, end_date=end_date),
        )
        return response.content

    def export_comparisons(self) -> bytes:
        response = self._request("GET", "/exports/bill-comparisons.csv")
        return response.content


client = ElectricityApiClient()
