"""Database models for Person B's subscription manager."""

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


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_subscriptions_amount_positive"),
        CheckConstraint(
            "billing_cycle IN ('weekly', 'monthly', 'quarterly', 'yearly', 'custom')",
            name="ck_subscriptions_cycle",
        ),
        CheckConstraint(
            "status IN ('active', 'paused', 'cancelled', 'expired')",
            name="ck_subscriptions_status",
        ),
        CheckConstraint(
            "billing_cycle != 'custom' OR custom_interval_days IS NOT NULL",
            name="ck_subscriptions_custom_days",
        ),
        CheckConstraint(
            "reminder_days_before >= 0 AND reminder_days_before <= 365",
            name="ck_subscriptions_reminder_days",
        ),
        Index("ix_subscription_status_renewal", "status", "next_renewal_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    service_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False)
    custom_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_renewal_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payment_method: Mapped[str] = mapped_column(
        String(40), default="other", nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reminder_days_before: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    payments: Mapped[list["SubscriptionPayment"]] = relationship(
        back_populates="subscription", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["RenewalReminder"]] = relationship(
        back_populates="subscription", cascade="all, delete-orphan"
    )


class SubscriptionPayment(Base):
    """An actual payment recorded by the user. No payment provider is integrated."""

    __tablename__ = "subscription_payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        UniqueConstraint("idempotency_key", name="uq_payments_idempotency"),
        UniqueConstraint(
            "subscription_id", "billing_period", name="uq_payment_subscription_period"
        ),
        Index("ix_payments_paid_on", "paid_on"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period: Mapped[str] = mapped_column(String(7), nullable=False)
    payment_method: Mapped[str] = mapped_column(
        String(40), default="other", nullable=False
    )
    reference: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    subscription: Mapped[Subscription] = relationship(back_populates="payments")


class RenewalReminder(Base):
    __tablename__ = "renewal_reminders"
    __table_args__ = (
        UniqueConstraint(
            "subscription_id", "renewal_date", name="uq_reminder_subscription_date"
        ),
        Index("ix_reminders_status_date", "status", "renewal_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    renewal_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    subscription: Mapped[Subscription] = relationship(back_populates="reminders")


class IntegrationSyncState(Base):
    __tablename__ = "integration_sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    destination: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="never", nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    records_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_period: Mapped[str | None] = mapped_column(String(7), nullable=True)
    last_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
