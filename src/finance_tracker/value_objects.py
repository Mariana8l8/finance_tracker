"""Immutable value objects for the finance tracker domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, order=True)
class Money:
    """A non-negative money amount in a selected currency."""

    amount: float
    currency: str = "UAH"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative.")
        if not self.currency.strip():
            raise ValueError("Currency must not be empty.")

    def _assert_same_currency(
        self,
        other: "Money",
    ) -> None:
        if self.currency != other.currency:
            raise ValueError("Currency mismatch.")

    def __add__(
        self,
        other: "Money",
    ) -> "Money":
        self._assert_same_currency(other)
        return Money(
            self.amount + other.amount,
            self.currency,
        )

    def __sub__(
        self,
        other: "Money",
    ) -> "Money":
        self._assert_same_currency(other)
        if self.amount < other.amount:
            raise ValueError("Money result cannot be negative.")
        return Money(
            self.amount - other.amount,
            self.currency,
        )

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"


@dataclass(frozen=True, slots=True)
class SignedMoney:
    """A signed amount used for balances."""

    amount: float
    currency: str = "UAH"

    def __add__(
        self,
        other: "SignedMoney",
    ) -> "SignedMoney":
        if self.currency != other.currency:
            raise ValueError("Currency mismatch.")
        return SignedMoney(
            self.amount + other.amount,
            self.currency,
        )

    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"
