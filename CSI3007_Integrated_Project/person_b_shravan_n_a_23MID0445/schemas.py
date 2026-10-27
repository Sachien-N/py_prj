"""Pydantic contracts for Person B."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BILLING_CYCLES = ("weekly", "monthly", "quarterly", "yearly", "custom")
STATUSES = ("active", "paused", "cancelled", "expired")
PAYMENT_METHODS = ("cash", "card", "upi", "net_banking", "other")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SubscriptionCreate(StrictModel):
    service_name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=60)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = "INR"
    billing_cycle: Literal["weekly", "monthly", "quarterly", "yearly", "custom"]
    custom_interval_days: int | None = Field(default=None, ge=1, le=3650)
    start_date: date
    next_renewal_date: date | None = None
    payment_method: str = "other"
    status: Literal["active", "paused", "cancelled", "expired"] = "active"
    notes: str = Field(default="", max_length=1000)
    reminder_days_before: int = Field(default=7, ge=0, le=365)

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, value: str) -> str:
        value = value.upper().strip()
        if not CURRENCY_RE.match(value):
            raise ValueError("currency must be a three-letter ISO code")
        return value

    @field_validator("payment_method")
    @classmethod
    def clean_payment_method(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in PAYMENT_METHODS:
            raise ValueError("Unsupported payment method")
        return value

    @model_validator(mode="after")
    def validate_cycle(self):
        if self.billing_cycle == "custom" and not self.custom_interval_days:
            raise ValueError("custom_interval_days is required for a custom cycle")
        if self.billing_cycle != "custom":
            self.custom_interval_days = None
        if self.next_renewal_date and self.next_renewal_date < self.start_date:
            raise ValueError("next_renewal_date cannot be before start_date")
        return self


class SubscriptionUpdate(StrictModel):
    service_name: str | None = Field(default=None, min_length=1, max_length=160)
    category: str | None = Field(default=None, min_length=1, max_length=60)
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    currency: str | None = None
    billing_cycle: Literal["weekly", "monthly", "quarterly", "yearly", "custom"] | None = None
    custom_interval_days: int | None = Field(default=None, ge=1, le=3650)
    start_date: date | None = None
    next_renewal_date: date | None = None
    payment_method: str | None = None
    status: Literal["active", "paused", "cancelled", "expired"] | None = None
    notes: str | None = Field(default=None, max_length=1000)
    reminder_days_before: int | None = Field(default=None, ge=0, le=365)

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.upper().strip()
        if not CURRENCY_RE.match(value):
            raise ValueError("currency must be a three-letter ISO code")
        return value

    @field_validator("payment_method")
    @classmethod
    def clean_payment_method(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.lower().strip()
        if value not in PAYMENT_METHODS:
            raise ValueError("Unsupported payment method")
        return value


class PaymentCreate(StrictModel):
    subscription_id: int = Field(ge=1)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    paid_on: date
    billing_period: str | None = None
    payment_method: str = "other"
    reference: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=1000)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=160)
    currency: str | None = None

    @field_validator("billing_period")
    @classmethod
    def validate_period(cls, value: str | None) -> str | None:
        if value is not None and not MONTH_RE.match(value):
            raise ValueError("billing_period must use YYYY-MM format")
        return value

    @field_validator("payment_method")
    @classmethod
    def clean_payment_method(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in PAYMENT_METHODS:
            raise ValueError("Unsupported payment method")
        return value

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.upper().strip()
        if not CURRENCY_RE.match(value):
            raise ValueError("currency must be a three-letter ISO code")
        return value
