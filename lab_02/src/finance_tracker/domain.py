"""Object-oriented domain model for the finance tracker."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Iterator

from finance_tracker.value_objects import Money, SignedMoney


class TransactionType(str, Enum):
    """Supported transaction types."""

    INCOME = "income"
    EXPENSE = "expense"


@dataclass(frozen=True, slots=True)
class Category:
    """Finance category value object."""

    name: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Category name must not be empty.")

    def __str__(self) -> str:
        return self.name


@dataclass(slots=True)
class Transaction(ABC):
    """Base abstract transaction."""

    id: int
    occurred_on: date
    category: Category
    amount: Money
    description: str

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError("Transaction id must be positive.")
        if not self.description.strip():
            raise ValueError("Description must not be empty.")

    @property
    @abstractmethod
    def transaction_type(self) -> TransactionType:
        """Return concrete transaction type."""

    @property
    @abstractmethod
    def signed_amount(self) -> SignedMoney:
        """Return transaction amount with accounting sign."""

    def __str__(self) -> str:
        return (
            f"{self.id}: {self.occurred_on.isoformat()} "
            f"{self.category} {self.transaction_type.value} {self.amount}"
        )


@dataclass(slots=True)
class Income(Transaction):
    """Income transaction."""

    @property
    def transaction_type(self) -> TransactionType:
        return TransactionType.INCOME

    @property
    def signed_amount(self) -> SignedMoney:
        return SignedMoney(
            self.amount.amount,
            self.amount.currency,
        )


@dataclass(slots=True)
class Expense(Transaction):
    """Expense transaction."""

    @property
    def transaction_type(self) -> TransactionType:
        return TransactionType.EXPENSE

    @property
    def signed_amount(self) -> SignedMoney:
        return SignedMoney(
            -self.amount.amount,
            self.amount.currency,
        )


@dataclass(slots=True)
class Budget:
    """Budget aggregate that owns transactions and category limits."""

    id: int
    name: str
    currency: str = "UAH"
    _transactions: list[Transaction] = field(default_factory=list)
    _category_limits: dict[Category, Money] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.id <= 0:
            raise ValueError("Budget id must be positive.")
        if not self.name.strip():
            raise ValueError("Budget name must not be empty.")

    def add_transaction(
        self,
        transaction: Transaction,
    ) -> None:
        """Add a transaction to the budget."""

        if transaction.amount.currency != self.currency:
            raise ValueError("Transaction currency does not match budget currency.")
        self._transactions.append(transaction)

    def set_category_limit(
        self,
        category: Category,
        limit: Money,
    ) -> None:
        """Set spending limit for a category."""

        if limit.currency != self.currency:
            raise ValueError("Limit currency does not match budget currency.")
        self._category_limits[category] = limit

    @property
    def transactions(self) -> tuple[Transaction, ...]:
        """Expose transactions as immutable tuple."""

        return tuple(self._transactions)

    @property
    def balance(self) -> SignedMoney:
        """Calculate current budget balance."""

        total = sum(transaction.signed_amount.amount for transaction in self._transactions)
        return SignedMoney(total, self.currency)

    def spent_by_category(
        self,
        category: Category,
    ) -> Money:
        """Calculate expenses in a selected category."""

        total = sum(
            transaction.amount.amount
            for transaction in self._transactions
            if isinstance(transaction, Expense) and transaction.category == category
        )
        return Money(total, self.currency)

    def is_limit_exceeded(
        self,
        category: Category,
    ) -> bool:
        """Return whether a selected category exceeds its limit."""

        limit = self._category_limits.get(category)
        if limit is None:
            return False
        return self.spent_by_category(category) > limit

    def __len__(self) -> int:
        return len(self._transactions)

    def __iter__(self) -> Iterator[Transaction]:
        return iter(self._transactions)

    def __contains__(
        self,
        transaction_id: int,
    ) -> bool:
        return any(transaction.id == transaction_id for transaction in self._transactions)

    def __getitem__(
        self,
        transaction_id: int,
    ) -> Transaction:
        for transaction in self._transactions:
            if transaction.id == transaction_id:
                return transaction
        raise KeyError(transaction_id)
