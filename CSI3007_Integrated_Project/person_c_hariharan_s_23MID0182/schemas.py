"""Pydantic contracts for Person C's electricity API."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SocketCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    appliance: str = Field(min_length=1, max_length=120)
    rated_power_w: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    location: str = Field(default="", max_length=120)
    is_active: bool = True
    adapter_type: Literal["manual", "simulated", "future_vendor", "mqtt"] = "manual"

    @field_validator("name", "appliance")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        value = " ".join(value.split())
        if not value:
            raise ValueError("This field cannot be blank")
        return value


class SocketUpdate(StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    appliance: str | None = Field(default=None, min_length=1, max_length=120)
    rated_power_w: Decimal | None = Field(
        default=None, gt=0, max_digits=10, decimal_places=2
    )
    location: str | None = Field(default=None, max_length=120)
    is_active: bool | None = None
    adapter_type: Literal["manual", "simulated", "future_vendor", "mqtt"] | None = None


class ReadingCreate(StrictModel):
    socket_id: int = Field(ge=1)
    reading_at: datetime
    power_w: Decimal = Field(ge=0, le=100000, max_digits=10, decimal_places=2)
    cumulative_energy_kwh: Decimal | None = Field(
        default=None, ge=0, max_digits=12, decimal_places=3
    )
    source: Literal["manual", "simulated", "adapter"] = "manual"
    notes: str = Field(default="", max_length=240)

    @field_validator("reading_at")
    @classmethod
    def require_aware_and_not_future(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("reading_at must include a timezone offset, e.g. +05:30")
        if value.astimezone(timezone.utc) > datetime.now(timezone.utc) + timedelta(
            minutes=5
        ):
            raise ValueError("reading_at cannot be more than 5 minutes in the future")
        return value


class TariffSlabCreate(StrictModel):
    from_units: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    to_units: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    rate_per_unit: Decimal = Field(ge=0, max_digits=8, decimal_places=4)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.to_units is not None and self.to_units <= self.from_units:
            raise ValueError("to_units must be greater than from_units")
        return self


class TariffComponentCreate(StrictModel):
    name: str = Field(min_length=1, max_length=120)
    charge_type: Literal["fixed_monthly", "per_unit", "percent_of_energy"]
    amount: Decimal = Field(ge=0, max_digits=12, decimal_places=4)
    sort_order: int = Field(default=0, ge=0, le=100)


class TariffCreate(StrictModel):
    name: str = Field(min_length=1, max_length=180)
    category: str = Field(default="domestic", min_length=1, max_length=60)
    currency: str = "INR"
    effective_from: date
    effective_to: date | None = None
    source: str = Field(min_length=1, max_length=500)
    source_url: str = Field(default="", max_length=500)
    is_verified: bool = False
    is_active: bool = True
    notes: str = Field(default="", max_length=2000)
    slabs: list[TariffSlabCreate] = Field(min_length=1, max_length=20)
    components: list[TariffComponentCreate] = Field(default_factory=list, max_length=20)

    @field_validator("currency")
    @classmethod
    def clean_currency(cls, value: str) -> str:
        value = value.upper().strip()
        if not CURRENCY_RE.match(value):
            raise ValueError("currency must be a three-letter ISO code")
        return value

    @model_validator(mode="after")
    def validate_dates_and_slabs(self):
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to cannot be before effective_from")
        slabs = sorted(self.slabs, key=lambda item: item.from_units)
        if slabs[0].from_units != 0:
            raise ValueError("The first tariff slab must start at 0 units")
        for index, slab in enumerate(slabs):
            if index < len(slabs) - 1:
                if slab.to_units is None:
                    raise ValueError("Only the final slab may have no upper bound")
                if slabs[index + 1].from_units != slab.to_units:
                    raise ValueError("Tariff slabs must be contiguous with no gaps")
            elif slab.to_units is None:
                continue
        if any(
            slab.to_units is None for slab in slabs[:-1]
        ):
            raise ValueError("Only the final slab may have no upper bound")
        self.slabs = slabs
        return self


class TariffUpdate(StrictModel):
    is_active: bool | None = None
    is_verified: bool | None = None
    source: str | None = Field(default=None, min_length=1, max_length=500)
    source_url: str | None = Field(default=None, max_length=500)
    effective_to: date | None = None
    notes: str | None = Field(default=None, max_length=2000)


class BillCreate(StrictModel):
    bill_reference: str = Field(min_length=1, max_length=120)
    billing_period_start: date
    billing_period_end: date
    billed_units: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    bill_amount: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    fixed_charges: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    other_charges: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    bill_date: date
    source: str = Field(default="manual", max_length=120)
    notes: str = Field(default="", max_length=2000)

    @model_validator(mode="after")
    def validate_period(self):
        if self.billing_period_end < self.billing_period_start:
            raise ValueError("billing_period_end cannot be before billing_period_start")
        if (self.billing_period_end - self.billing_period_start).days > 120:
            raise ValueError("Billing period cannot exceed 120 days")
        return self


class DemoSeedRequest(StrictModel):
    months: int = Field(default=6, ge=1, le=12)
    force: bool = False
