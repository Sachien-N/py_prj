"""HTTP client used by Person B's dashboard."""

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


class SubscriptionApiClient:
    def __init__(self, base_url: str | None = None, timeout: float = 12.0):
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
            raise ApiError("The subscription API timed out. Is the API server running?")
        except requests.ConnectionError:
            raise ApiError(
                "Cannot reach the subscription API at "
                f"{self.base_url}. Start it with: python -m uvicorn api:app --port 8002"
            )
        except requests.RequestException:
            raise ApiError("The subscription API request failed safely.")
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

    def categories(self) -> list[str]:
        return self._request("GET", "/meta/categories")

    def subscriptions(self, **filters) -> list[dict]:
        params = {key: value for key, value in filters.items() if value not in (None, "")}
        return self._request("GET", "/subscriptions", params=params)

    def subscription(self, subscription_id: int) -> dict:
        return self._request("GET", f"/subscriptions/{subscription_id}")

    def create_subscription(self, payload: dict) -> dict:
        return self._request("POST", "/subscriptions", json=payload)

    def update_subscription(self, subscription_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/subscriptions/{subscription_id}", json=payload)

    def delete_subscription(self, subscription_id: int) -> None:
        self._request("DELETE", f"/subscriptions/{subscription_id}")

    def advance_renewal(self, subscription_id: int) -> dict:
        return self._request("POST", f"/subscriptions/{subscription_id}/advance-renewal")

    def summary(self) -> dict:
        return self._request("GET", "/subscriptions/summary")

    def upcoming(self, days: int = 30) -> dict:
        return self._request("GET", "/subscriptions/upcoming", params={"days": days})

    def payments(self, **filters) -> list[dict]:
        params = {key: value for key, value in filters.items() if value not in (None, "")}
        return self._request("GET", "/subscriptions/payments", params=params)

    def record_payment(self, payload: dict) -> dict:
        return self._request("POST", "/subscriptions/payments", json=payload)

    def delete_payment(self, payment_id: int) -> None:
        self._request("DELETE", f"/subscriptions/payments/{payment_id}")

    def refresh_reminders(self) -> dict:
        return self._request("POST", "/subscriptions/reminders/refresh")

    def reminders(self) -> list[dict]:
        return self._request("GET", "/subscriptions/reminders")

    def dismiss_reminder(self, reminder_id: int) -> dict:
        return self._request("POST", f"/subscriptions/reminders/{reminder_id}/dismiss")

    def export_csv(self) -> bytes:
        response = self._request("GET", "/subscriptions/export.csv")
        return response.content

    def integration_status(self, check_remote: bool = False) -> dict:
        return self._request(
            "GET",
            "/integrations/person-a/status",
            params={"check_remote": str(check_remote).lower()},
            timeout=10,
        )

    def sync_person_a(self, period: str | None = None) -> dict:
        params = {"period": period} if period else None
        return self._request(
            "POST",
            "/integrations/person-a/sync",
            headers=self.integration_headers,
            params=params,
            timeout=35,
        )

    def payload(self, period: str | None = None) -> dict:
        params = {"period": period} if period else None
        return self._request(
            "GET",
            "/integrations/person-a/payload",
            headers=self.integration_headers,
            params=params,
        )


client = SubscriptionApiClient()
