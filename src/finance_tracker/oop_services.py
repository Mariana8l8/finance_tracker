"""Application service layer for the OOP finance tracker model."""

from __future__ import annotations

from datetime import date

from finance_tracker.domain import Budget, Category, Expense, Income, Transaction
from finance_tracker.dto import TransactionPayload
from finance_tracker.policies import BudgetAlertPolicy
from finance_tracker.protocols import BudgetExporter, Notifier
from finance_tracker.repositories import InMemoryRepository
from finance_tracker.value_objects import Money


class JsonBudgetExporter:
    """Demo exporter compatible with BudgetExporter protocol."""

    def export(
        self,
        budget: Budget,
    ) -> str:
        transactions = [
            {
                "id": transaction.id,
                "date": transaction.occurred_on.isoformat(),
                "type": transaction.transaction_type.value,
                "category": transaction.category.name,
                "amount": transaction.amount.amount,
                "description": transaction.description,
            }
            for transaction in budget
        ]
        return {
            "id": budget.id,
            "name": budget.name,
            "balance": budget.balance.amount,
            "transactions": transactions,
        }.__repr__()


class ConsoleNotifier:
    """Demo notifier compatible with Notifier protocol."""

    def send(
        self,
        recipient: str,
        message: str,
    ) -> None:
        print(f"Notification to {recipient}: {message}")


class FinanceTrackerService:
    """Application service orchestrating budget use cases."""

    def __init__(
        self,
        budget_repository: InMemoryRepository[Budget],
        exporter: BudgetExporter,
        notifier: Notifier,
        alert_policy: BudgetAlertPolicy,
    ) -> None:
        self._budgets = budget_repository
        self._exporter = exporter
        self._notifier = notifier
        self._alert_policy = alert_policy

    def create_budget(
        self,
        budget_id: int,
        name: str,
        currency: str = "UAH",
    ) -> Budget:
        budget = Budget(
            id=budget_id,
            name=name,
            currency=currency,
        )
        self._budgets.add(budget)
        return budget

    def add_transaction(
        self,
        budget_id: int,
        payload: TransactionPayload,
        recipient: str,
    ) -> Transaction:
        budget = self._require_budget(budget_id)
        transaction = transaction_from_payload(payload, budget.currency)
        budget.add_transaction(transaction)

        if self._alert_policy.should_alert(budget, transaction.category):
            self._notifier.send(
                recipient,
                f"Budget limit exceeded for {transaction.category}.",
            )

        return transaction

    def export_budget(
        self,
        budget_id: int,
    ) -> str:
        budget = self._require_budget(budget_id)
        return self._exporter.export(budget)

    def _require_budget(
        self,
        budget_id: int,
    ) -> Budget:
        budget = self._budgets.get(budget_id)
        if budget is None:
            raise ValueError(f"Budget {budget_id} was not found.")
        return budget


def transaction_from_payload(
    payload: TransactionPayload,
    currency: str,
) -> Transaction:
    """Convert external TypedDict payload into a domain transaction."""

    amount = Money(
        amount=payload["amount"],
        currency=currency,
    )
    category = Category(payload["category"])
    description = payload.get("description", "No description")
    occurred_on = date.fromisoformat(payload["date"])

    if payload["type"] == "income":
        return Income(
            id=payload["id"],
            occurred_on=occurred_on,
            category=category,
            amount=amount,
            description=description,
        )

    return Expense(
        id=payload["id"],
        occurred_on=occurred_on,
        category=category,
        amount=amount,
        description=description,
    )

