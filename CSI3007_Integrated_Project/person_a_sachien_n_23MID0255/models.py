"""Database models for Person A's expense manager."""

from __future__ import annotations

import json
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


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    keywords: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    color: Mapped[str] = mapped_column(String(9), default="#64748b", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    expenses: Mapped[list["Expense"]] = relationship(back_populates="category")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="category")

    @property
    def keyword_list(self) -> list[str]:
        try:
            value = json.loads(self.keywords or "[]")
        except json.JSONDecodeError:
            return []
        return [str(item) for item in value] if isinstance(value, list) else []


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_expenses_amount_positive"),
        CheckConstraint(
            "transaction_type IN ('expense', 'refund')",
            name="ck_expenses_transaction_type",
        ),
        UniqueConstraint("source_app", "external_id", name="uq_expense_source_external"),
        Index("ix_expenses_date_type", "expense_date", "transaction_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    merchant: Mapped[str] = mapped_column(String(200), nullable=False)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    payment_method: Mapped[str] = mapped_column(
        String(40), default="other", nullable=False
    )
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    transaction_type: Mapped[str] = mapped_column(
        String(20), default="expense", nullable=False
    )
    refund_of_expense_id: Mapped[int | None] = mapped_column(
        ForeignKey("expenses.id", ondelete="SET NULL"), nullable=True
    )
    source_app: Mapped[str] = mapped_column(
        String(30), default="local", nullable=False, index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    category: Mapped[Category] = relationship(back_populates="expenses")
    refund_of: Mapped["Expense | None"] = relationship(remote_side=[id])


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_budgets_amount_positive"),
        Index("ix_budgets_month", "month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    notes: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    category: Mapped[Category | None] = relationship(back_populates="budgets")


class ImportedExternalExpense(Base):
    """Audit record for expenses received from another application."""

    __tablename__ = "imported_external_expenses"
    __table_args__ = (
        UniqueConstraint(
            "source_app", "external_id", name="uq_import_source_external"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_app: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(160), nullable=False)
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )


class IntegrationSyncState(Base):
    __tablename__ = "integration_sync_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="never", nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    items_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
