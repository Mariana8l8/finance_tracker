from datetime import date
from unittest import TestCase, main

from finance_tracker.domain import Budget, Category, Expense, Income
from finance_tracker.oop_services import FinanceTrackerService, transaction_from_payload
from finance_tracker.policies import CategoryLimitAlertPolicy
from finance_tracker.protocols import BudgetExporter, Notifier
from finance_tracker.repositories import InMemoryRepository
from finance_tracker.value_objects import Money, SignedMoney


class FakeExporter:
    def export(
        self,
        budget: Budget,
    ) -> str:
        return f"budget:{budget.id}:{len(budget)}"


class FakeNotifier:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(
        self,
        recipient: str,
        message: str,
    ) -> None:
        self.messages.append(f"{recipient}:{message}")


class TestOopDomain(TestCase):
    def test_money_value_object_and_dunder_methods(self) -> None:
        first = Money(100.0)
        second = Money(50.0)

        self.assertEqual(first + second, Money(150.0))
        self.assertEqual(first - second, Money(50.0))
        self.assertEqual(str(first), "100.00 UAH")

        with self.assertRaises(ValueError):
            Money(-1.0)

    def test_income_expense_and_budget_collection(self) -> None:
        salary = Income(
            id=1,
            occurred_on=date(2026, 9, 1),
            category=Category("Salary"),
            amount=Money(1000.0),
            description="Salary",
        )
        food = Expense(
            id=2,
            occurred_on=date(2026, 9, 2),
            category=Category("Food"),
            amount=Money(250.0),
            description="Groceries",
        )
        budget = Budget(id=1, name="Demo")
        budget.add_transaction(salary)
        budget.add_transaction(food)

        self.assertEqual(len(budget), 2)
        self.assertIn(2, budget)
        self.assertEqual(budget[2], food)
        self.assertEqual(list(budget), [salary, food])
        self.assertEqual(budget.balance, SignedMoney(750.0))

    def test_category_limit_policy_and_repository(self) -> None:
        food = Category("Food")
        budget = Budget(id=1, name="Demo")
        budget.set_category_limit(food, Money(100.0))
        budget.add_transaction(
            Expense(
                id=1,
                occurred_on=date(2026, 9, 2),
                category=food,
                amount=Money(150.0),
                description="Groceries",
            )
        )
        repository: InMemoryRepository[Budget] = InMemoryRepository()
        repository.add(budget)
        policy = CategoryLimitAlertPolicy()

        self.assertEqual(repository.get(1), budget)
        self.assertTrue(policy.should_alert(budget, food))

    def test_service_dependency_injection_and_protocols(self) -> None:
        repository: InMemoryRepository[Budget] = InMemoryRepository()
        exporter = FakeExporter()
        notifier = FakeNotifier()
        service = FinanceTrackerService(
            budget_repository=repository,
            exporter=exporter,
            notifier=notifier,
            alert_policy=CategoryLimitAlertPolicy(),
        )
        budget = service.create_budget(1, "September")
        food = Category("Food")
        budget.set_category_limit(food, Money(100.0))

        service.add_transaction(
            1,
            {
                "id": 1,
                "date": "2026-09-03",
                "type": "expense",
                "category": "Food",
                "amount": 150.0,
                "description": "Groceries",
            },
            "student@example.com",
        )

        self.assertIsInstance(exporter, BudgetExporter)
        self.assertIsInstance(notifier, Notifier)
        self.assertEqual(service.export_budget(1), "budget:1:1")
        self.assertEqual(len(notifier.messages), 1)

    def test_transaction_payload_conversion(self) -> None:
        transaction = transaction_from_payload(
            {
                "id": 10,
                "date": "2026-09-05",
                "type": "income",
                "category": "Freelance",
                "amount": 500.0,
                "description": "Project",
            },
            "UAH",
        )

        self.assertIsInstance(transaction, Income)
        self.assertEqual(transaction.signed_amount, SignedMoney(500.0))


if __name__ == "__main__":
    main()

