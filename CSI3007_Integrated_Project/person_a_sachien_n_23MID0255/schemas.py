"""Pydantic request/response contracts for Person A."""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PAYMENT_METHODS = {"cash", "card", "upi", "net_banking", "other"}
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class CategoryCreate(StrictModel):
    name: str = Field(min_length=1, max_length=60)
    description: str = Field(default="", max_length=240)
    keywords: list[str] = Field(default_factory=list, max_length=50)
    color: str = Field(default="#64748b", pattern=r"^#[0-9a-fA-F]{6}$")
    priority: int = Field(default=50, ge=0, le=100)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Category name cannot be blank")
        return value

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            value = " ".join(value.lower().split())
            if value and value not in cleaned:
                cleaned.append(value)
        return cleaned


class CategoryUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    description: str | None = Field(default=None, max_length=240)
    keywords: list[str] | None = Field(default=None, max_length=50)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    priority: int | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        if not value:
            raise ValueError("Category name cannot be blank")
        return value

    @field_validator("keywords")
    @classmethod
    def clean_keywords(cls, values: list[str] | None) -> list[str] | None:
        if values is None:
            return None
        cleaned = []
        for value in values:
            value = " ".join(value.lower().split())
            if value and value not in cleaned:
                cleaned.append(value)
        return cleaned


class ExpenseCreate(StrictModel):
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    expense_date: date
    merchant: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=60)
    payment_method: str = "other"
    description: str = Field(default="", max_length=1000)
    transaction_type: Literal["expense", "refund"] = "expense"
    refund_of_expense_id: int | None = Field(default=None, ge=1)
    currency: str = "INR"
    auto_categorize: bool = True

    @field_validator("merchant")
    @classmethod
    def clean_merchant(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("Merchant cannot be blank")
        return value

    @field_validator("payment_method")
    @classmethod
    def clean_payment_method(cls, value: str) -> str:
        value = value.lower().strip()
        if value not in PAYMENT_METHODS:
            raise ValueError(
                "payment_method must be one of: " + ", ".join(sorted(PAYMENT_METHODS))
            )
        return value

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, value: str) -> str:
        value = value.upper().strip()
        if not CURRENCY_RE.match(value):
            raise ValueError("currency must be a three-letter ISO code")
        return value

    @model_validator(mode="after")
    def validate_refund_reference(self):
        if self.transaction_type == "expense" and self.refund_of_expense_id:
            raise ValueError("refund_of_expense_id is only valid for refunds")
        return self


class ExpenseUpdate(StrictModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    expense_date: date | None = None
    merchant: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=60)
    payment_method: str | None = None
    description: str | None = Field(default=None, max_length=1000)
    transaction_type: Literal["expense", "refund"] | None = None
    refund_of_expense_id: int | None = Field(default=None, ge=1)
    currency: str | None = None
    auto_categorize: bool | None = None

    @field_validator("merchant")
    @classmethod
    def clean_merchant(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = " ".join(value.split())
        if not value:
            raise ValueError("Merchant cannot be blank")
        return value

    @field_validator("payment_method")
    @classmethod
    def clean_payment_method(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.lower().strip()
        if value not in PAYMENT_METHODS:
            raise ValueError(
                "payment_method must be one of: " + ", ".join(sorted(PAYMENT_METHODS))
            )
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


class BudgetCreate(StrictModel):
    month: str
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    category: str | None = Field(default=None, max_length=60)
    notes: str = Field(default="", max_length=240)

    @field_validator("month")
    @classmethod
    def validate_month(cls, value: str) -> str:
        if not MONTH_RE.match(value):
            raise ValueError("month must use YYYY-MM format")
        return value


class BudgetUpdate(StrictModel):
    amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    category: str | None = Field(default=None, max_length=60)
    notes: str | None = Field(default=None, max_length=240)


class SubscriptionExpenseRecord(StrictModel):
    source_app: Literal["person_b"]
    external_id: str = Field(min_length=1, max_length=160)
    subscription_id: int | None = None
    service_name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=60)
    amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = "INR"
    billing_period: str
    billing_date: date
    record_updated_at: datetime
    is_estimate: bool = True
    description: str = Field(default="", max_length=1000)

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, value: str) -> str:
        value = value.upper().strip()
        if not CURRENCY_RE.match(value):
            raise ValueError("currency must be a three-letter ISO code")
        return value

    @field_validator("billing_period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        if not MONTH_RE.match(value):
            raise ValueError("billing_period must use YYYY-MM format")
        return value


class SubscriptionSyncRequest(StrictModel):
    source_app: Literal["person_b"]
    generated_at: datetime
    billing_period: str
    summary: dict[str, Any] = Field(default_factory=dict)
    expense_records: list[SubscriptionExpenseRecord] = Field(
        default_factory=list, max_length=1000
    )

    @field_validator("billing_period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        if not MONTH_RE.match(value):
            raise ValueError("billing_period must use YYYY-MM format")
        return value


class ElectricityExpenseRecord(StrictModel):
    source_app: Literal["person_c"]
    external_id: str = Field(min_length=1, max_length=160)
    period: str
    billing_date: date
    expense_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    currency: str = "INR"
    units: Decimal | None = Field(default=None, ge=0)
    is_estimate: bool = True
    description: str = Field(default="", max_length=1000)
    record_updated_at: datetime
    data_coverage_pct: Decimal | None = Field(default=None, ge=0, le=100)

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, value: str) -> str:
        value = value.upper().strip()
        if not CURRENCY_RE.match(value):
            raise ValueError("currency must be a three-letter ISO code")
        return value

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        if not MONTH_RE.match(value):
            raise ValueError("period must use YYYY-MM format")
        return value


class ElectricitySyncRequest(StrictModel):
    source_app: Literal["person_c"]
    generated_at: datetime
    summary: dict[str, Any] = Field(default_factory=dict)
    expense_records: list[ElectricityExpenseRecord] = Field(
        default_factory=list, max_length=1200
    )
