from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from finance_tracker.domain import Budget, Category
from finance_tracker.value_objects import Money, SignedMoney


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        pytest.param(10.0, 5.0, 15.0, id="small-values"),
        pytest.param(0.0, 0.0, 0.0, id="zero-boundary"),
        pytest.param(1_000_000.25, 0.75, 1_000_001.0, id="large-values"),
    ],
)
def test_money_addition_uses_approx(
    left: float,
    right: float,
    expected: float,
) -> None:
    result = Money(left) + Money(right)

    assert result.amount == pytest.approx(expected)
    assert result.currency == "UAH"


@pytest.mark.parametrize(
    "amount",
    [
        pytest.param(-0.01, id="below-zero"),
        pytest.param(-100.0, id="negative"),
    ],
)
def test_money_rejects_negative_amounts(amount: float) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        Money(amount)


def test_money_is_frozen_value_object() -> None:
    money = Money(10.0)

    with pytest.raises(FrozenInstanceError):
        money.amount = 20.0  # type: ignore[misc]


def test_money_rejects_currency_mismatch() -> None:
    with pytest.raises(ValueError, match="Currency mismatch"):
        Money(10.0, "UAH") + Money(10.0, "USD")


def test_signed_money_rejects_currency_mismatch() -> None:
    with pytest.raises(ValueError, match="Currency mismatch"):
        SignedMoney(10.0, "UAH") + SignedMoney(-5.0, "USD")


def test_budget_getitem_missing_transaction_raises() -> None:
    budget = Budget(id=1, name="Empty")

    with pytest.raises(KeyError):
        _ = budget[999]


def test_category_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        Category("   ")
