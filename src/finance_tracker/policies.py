"""Budget alert policies."""

from abc import ABC, abstractmethod

from finance_tracker.domain import Budget, Category


class BudgetAlertPolicy(ABC):
    """Abstract base class for budget alert policies."""

    @abstractmethod
    def should_alert(
        self,
        budget: Budget,
        category: Category,
    ) -> bool:
        """Return whether an alert should be sent."""


class CategoryLimitAlertPolicy(BudgetAlertPolicy):
    """Alert when category spending exceeds configured limit."""

    def should_alert(
        self,
        budget: Budget,
        category: Category,
    ) -> bool:
        return budget.is_limit_exceeded(category)

