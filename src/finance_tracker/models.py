"""Data models for the finance tracker application."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

OperationType = Literal["income", "expense"]


@dataclass(slots=True)
class Operation:
    """A single financial operation."""

    date: date
    category: str
    amount: float
    operation_type: OperationType

    def __post_init__(self) -> None:
        if not self.category.strip():
            raise ValueError("Category must not be empty.")

        if self.amount <= 0:
            raise ValueError("Amount must be greater than zero.")

        if self.operation_type not in {"income", "expense"}:
            raise ValueError("Operation type must be 'income' or 'expense'.")

    @property
    def signed_amount(self) -> float:
        """Return income as positive value and expense as negative value."""

        if self.operation_type == "income":
            return self.amount
        return -self.amount

