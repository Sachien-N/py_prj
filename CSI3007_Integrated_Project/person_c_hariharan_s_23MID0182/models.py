"""Database models for Person C's electricity monitoring system."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base, utcnow


class Socket(Base):
    __tablename__ = "sockets"
    __table_args__ = (
        CheckConstraint("rated_power_w > 0", name="ck_sockets_rated_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    appliance: Mapped[str] = mapped_column(String(120), nullable=False)
    rated_power_w: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    location: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    adapter_type: Mapped[str] = mapped_column(
        String(30), default="manual", nullable=False
    )
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    readings: Mapped[list["ElectricityReading"]] = relationship(
        back_populates="socket", cascade="all, delete-orphan"
    )


class ElectricityReading(Base):
    __tablename__ = "electricity_readings"
    __table_args__ = (
        CheckConstraint("power_w >= 0", name="ck_readings_power_nonnegative"),
        UniqueConstraint("socket_id", "reading_at", name="uq_reading_socket_time"),
        Index("ix_readings_socket_time", "socket_id", "reading_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    socket_id: Mapped[int] = mapped_column(
        ForeignKey("sockets.id", ondelete="CASCADE"), nullable=False
    )
    reading_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    power_w: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    cumulative_energy_kwh: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3), nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(30), default="manual", nullable=False
    )
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quality_flag: Mapped[str] = mapped_column(String(40), default="ok", nullable=False)
    out_of_order: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    socket: Mapped[Socket] = relationship(back_populates="readings")


class TariffConfig(Base):
    __tablename__ = "tariff_configs"
    __table_args__ = (
        CheckConstraint(
            "effective_to IS NULL OR effective_to >= effective_from",
            name="ck_tariff_effective_dates",
        ),
        Index("ix_tariffs_category_effective", "category", "effective_from"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    category: Mapped[str] = mapped_column(String(60), default="domestic", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    source: Mapped[str] = mapped_column(String(500), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    slabs: Mapped[list["TariffSlab"]] = relationship(
        back_populates="tariff", cascade="all, delete-orphan"
    )
    components: Mapped[list["TariffComponent"]] = relationship(
        back_populates="tariff", cascade="all, delete-orphan"
    )


class TariffSlab(Base):
    __tablename__ = "tariff_slabs"
    __table_args__ = (
        CheckConstraint("from_units >= 0", name="ck_slab_from_nonnegative"),
        CheckConstraint("to_units IS NULL OR to_units > from_units", name="ck_slab_range"),
        CheckConstraint("rate_per_unit >= 0", name="ck_slab_rate_nonnegative"),
        UniqueConstraint("tariff_id", "from_units", name="uq_slab_from"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tariff_id: Mapped[int] = mapped_column(
        ForeignKey("tariff_configs.id", ondelete="CASCADE"), nullable=False
    )
    from_units: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    to_units: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    rate_per_unit: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)

    tariff: Mapped[TariffConfig] = relationship(back_populates="slabs")


class TariffComponent(Base):
    __tablename__ = "tariff_components"
    __table_args__ = (
        CheckConstraint(
            "charge_type IN ('fixed_monthly', 'per_unit', 'percent_of_energy')",
            name="ck_component_type",
        ),
        CheckConstraint("amount >= 0", name="ck_component_amount"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tariff_id: Mapped[int] = mapped_column(
        ForeignKey("tariff_configs.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    charge_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    tariff: Mapped[TariffConfig] = relationship(back_populates="components")


class ElectricityBill(Base):
    __tablename__ = "electricity_bills"
    __table_args__ = (
        CheckConstraint("billed_units >= 0", name="ck_bill_units_nonnegative"),
        CheckConstraint("bill_amount >= 0", name="ck_bill_amount_nonnegative"),
        CheckConstraint(
            "billing_period_end >= billing_period_start", name="ck_bill_period"
        ),
        Index("ix_bills_period", "billing_period_start", "billing_period_end"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bill_reference: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    billed_units: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    bill_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    fixed_charges: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    other_charges: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False
    )
    bill_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(120), default="manual", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    comparison: Mapped["BillComparison | None"] = relationship(
        back_populates="bill", cascade="all, delete-orphan", uselist=False
    )


class BillComparison(Base):
    __tablename__ = "bill_comparisons"
    __table_args__ = (
        UniqueConstraint("bill_id", name="uq_comparison_bill"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bill_id: Mapped[int] = mapped_column(
        ForeignKey("electricity_bills.id", ondelete="CASCADE"), nullable=False
    )
    compared_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    estimated_units: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    actual_units: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    actual_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    unit_deviation: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    cost_deviation: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    percentage_deviation: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    tolerance_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    exceeds_tolerance: Mapped[bool] = mapped_column(Boolean, nullable=False)
    data_coverage_pct: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    tariff_id: Mapped[int | None] = mapped_column(
        ForeignKey("tariff_configs.id", ondelete="SET NULL"), nullable=True
    )
    analysis_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    bill: Mapped[ElectricityBill] = relationship(back_populates="comparison")


class IntegrationSyncState(Base):
    __tablename__ = "integration_sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    destination: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="never", nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    records_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_period: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
