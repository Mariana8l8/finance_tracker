"""Protocols for external finance tracker dependencies."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from finance_tracker.domain import Budget


@runtime_checkable
class BudgetExporter(Protocol):
    """Structural interface for budget exporters."""

    def export(
        self,
        budget: Budget,
    ) -> str:
        """Export budget data."""


@runtime_checkable
class Notifier(Protocol):
    """Structural interface for notification adapters."""

    def send(
        self,
        recipient: str,
        message: str,
    ) -> None:
        """Send a notification."""
