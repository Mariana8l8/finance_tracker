from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from finance_tracker.async_services import CurrencyConversionService
from finance_tracker.domain import Budget, Category
from finance_tracker.oop_services import FinanceTrackerService
from finance_tracker.policies import CategoryLimitAlertPolicy
from finance_tracker.protocols import BudgetExporter, Notifier
from finance_tracker.repositories import InMemoryRepository
from finance_tracker.value_objects import Money


def test_service_uses_exporter_return_value() -> None:
    repository: InMemoryRepository[Budget] = InMemoryRepository()
    budget = Budget(id=1, name="Demo")
    repository.add(budget)
    exporter = Mock(spec=BudgetExporter)
    exporter.export.return_value = "exported-budget"
    notifier = Mock(spec=Notifier)

    service = FinanceTrackerService(
        budget_repository=repository,
        exporter=exporter,
        notifier=notifier,
        alert_policy=CategoryLimitAlertPolicy(),
    )

    assert service.export_budget(1) == "exported-budget"
    exporter.export.assert_called_once_with(budget)


def test_service_notifies_when_limit_is_exceeded() -> None:
    repository: InMemoryRepository[Budget] = InMemoryRepository()
    notifier = Mock(spec=Notifier)
    service = FinanceTrackerService(
        budget_repository=repository,
        exporter=Mock(spec=BudgetExporter),
        notifier=notifier,
        alert_policy=CategoryLimitAlertPolicy(),
    )
    budget = service.create_budget(1, "September")
    budget.set_category_limit(Category("Food"), Money(50.0))

    service.add_transaction(
        1,
        {
            "id": 1,
            "date": "2026-09-12",
            "type": "expense",
            "category": "Food",
            "amount": 75.0,
            "description": "Groceries",
        },
        "student@example.com",
    )

    notifier.send.assert_called_once_with(
        "student@example.com",
        "Budget limit exceeded for Food.",
    )


def test_service_propagates_exporter_side_effect() -> None:
    repository: InMemoryRepository[Budget] = InMemoryRepository()
    repository.add(Budget(id=1, name="Demo"))
    exporter = Mock(spec=BudgetExporter)
    exporter.export.side_effect = RuntimeError("export unavailable")
    service = FinanceTrackerService(
        budget_repository=repository,
        exporter=exporter,
        notifier=Mock(spec=Notifier),
        alert_policy=CategoryLimitAlertPolicy(),
    )

    with pytest.raises(RuntimeError, match="export unavailable"):
        service.export_budget(1)


def test_async_currency_conversion_uses_async_provider() -> None:
    provider = AsyncMock()
    provider.get_rate.return_value = 0.025
    service = CurrencyConversionService(provider)

    result = asyncio.run(service.convert(Money(100.0, "UAH"), "USD"))

    assert result == Money(2.5, "USD")
    provider.get_rate.assert_awaited_once_with("UAH", "USD")


def test_async_currency_conversion_returns_same_currency_without_provider() -> None:
    provider = AsyncMock()
    service = CurrencyConversionService(provider)

    result = asyncio.run(service.convert(Money(100.0, "UAH"), "UAH"))

    assert result == Money(100.0, "UAH")
    provider.get_rate.assert_not_called()


def test_async_currency_conversion_rejects_invalid_rate() -> None:
    provider = AsyncMock()
    provider.get_rate.return_value = 0.0
    service = CurrencyConversionService(provider)

    with pytest.raises(ValueError, match="positive"):
        asyncio.run(service.convert(Money(100.0, "UAH"), "USD"))
