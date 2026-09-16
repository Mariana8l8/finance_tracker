"""Pydantic schemas for the Finance Tracker REST API."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BudgetCreate(BaseModel):
    """Request body for creating a budget."""

    name: str = Field(min_length=2, max_length=120)
    currency: str = Field(default="UAH", min_length=3, max_length=3)


class BudgetUpdate(BaseModel):
    """Request body for partially updating a budget."""

    name: str | None = Field(default=None, min_length=2, max_length=120)


class BudgetResponse(BaseModel):
    """Budget response model."""

    id: int
    name: str
    currency: str

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    """Request body for creating a category in a budget."""

    name: str = Field(min_length=1, max_length=120)
    spending_limit_amount: float | None = Field(default=None, ge=0)


class CategoryResponse(BaseModel):
    """Category response model."""

    id: int
    budget_id: int
    name: str
    spending_limit_amount: float | None

    model_config = ConfigDict(from_attributes=True)


class TransactionCreate(BaseModel):
    """Request body for creating a transaction."""

    category_id: int = Field(gt=0)
    occurred_on: date
    transaction_type: str = Field(pattern="^(income|expense)$")
    amount: float = Field(gt=0)
    description: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=255)


class TransactionUpdate(BaseModel):
    """Request body for partially updating a transaction."""

    amount: float | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=255)


class TransactionResponse(BaseModel):
    """Transaction response model."""

    id: int
    budget_id: int
    category_id: int
    occurred_on: date
    transaction_type: str
    amount: float
    description: str
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


class BudgetSummaryResponse(BaseModel):
    """Aggregated budget summary response."""

    budget_id: int
    balance: float
    income: float
    expenses: float
    category_counts: list[tuple[str, int]]


class BatchFetchRequest(BaseModel):
    """Request body for async HTTPX batch fetching."""

    urls: list[HttpUrl] = Field(min_length=1, max_length=20)
    timeout_seconds: float = Field(default=5.0, gt=0, le=30)
    attempts: int = Field(default=3, ge=1, le=5)
    concurrency_limit: int = Field(default=3, ge=1, le=10)
