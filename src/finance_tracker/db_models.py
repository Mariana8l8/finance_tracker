"""SQLAlchemy ORM models for finance tracker persistence."""

from __future__ import annotations

from datetime import date

from sqlalchemy import CheckConstraint, Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM mappings."""


class BudgetRecord(Base):
    """Persisted budget aggregate."""

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="UAH")

    categories: Mapped[list["CategoryRecord"]] = relationship(
        back_populates="budget",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["TransactionRecordORM"]] = relationship(
        back_populates="budget",
        cascade="all, delete-orphan",
    )


class CategoryRecord(Base):
    """Persisted finance category that belongs to a budget."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("budget_id", "name", name="uq_categories_budget_name"),
        CheckConstraint(
            "spending_limit_amount IS NULL OR spending_limit_amount >= 0",
            name="ck_categories_limit_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    spending_limit_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    budget: Mapped[BudgetRecord] = relationship(back_populates="categories")
    transactions: Mapped[list["TransactionRecordORM"]] = relationship(
        back_populates="category",
    )


class TransactionRecordORM(Base):
    """Persisted income or expense transaction."""

    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transactions_type_allowed",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    budget_id: Mapped[int] = mapped_column(
        ForeignKey("budgets.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
    )
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    budget: Mapped[BudgetRecord] = relationship(back_populates="transactions")
    category: Mapped[CategoryRecord] = relationship(back_populates="transactions")
