"""Small async service used to test async dependencies in laboratory work 6."""

from __future__ import annotations

from typing import Protocol

from finance_tracker.value_objects import Money


class AsyncRateProvider(Protocol):
    """External async exchange-rate provider boundary."""

    async def get_rate(
        self,
        source_currency: str,
        target_currency: str,
    ) -> float:
        """Return conversion rate between currencies."""


class CurrencyConversionService:
    """Convert Money values through an async provider."""

    def __init__(
        self,
        provider: AsyncRateProvider,
    ) -> None:
        self._provider = provider

    async def convert(
        self,
        money: Money,
        target_currency: str,
    ) -> Money:
        """Convert money into a target currency."""

        if money.currency == target_currency:
            return money

        rate = await self._provider.get_rate(
            money.currency,
            target_currency,
        )
        if rate <= 0:
            raise ValueError("Exchange rate must be positive.")

        return Money(
            amount=money.amount * rate,
            currency=target_currency,
        )
