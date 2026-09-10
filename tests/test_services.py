from datetime import date
from unittest import TestCase, main

from finance_tracker.models import Operation
from finance_tracker.services import (
    add_operation,
    calculate_balance,
    calculate_expenses,
    calculate_expenses_by_category,
    calculate_income,
    filter_by_category,
)


def create_operations() -> list[Operation]:
    return [
        Operation(date(2026, 9, 1), "Salary", 1000.0, "income"),
        Operation(date(2026, 9, 2), "Food", 150.0, "expense"),
        Operation(date(2026, 9, 3), "Transport", 50.0, "expense"),
        Operation(date(2026, 9, 4), "Food", 75.0, "expense"),
    ]


class TestFinanceServices(TestCase):
    def test_add_operation(self) -> None:
        operations = create_operations()
        add_operation(
            operations,
            Operation(date(2026, 9, 5), "Freelance", 500.0, "income"),
        )

        self.assertEqual(len(operations), 5)
        self.assertEqual(operations[-1].category, "Freelance")

    def test_calculate_income_expenses_and_balance(self) -> None:
        operations = create_operations()

        self.assertEqual(calculate_income(operations), 1000.0)
        self.assertEqual(calculate_expenses(operations), 275.0)
        self.assertEqual(calculate_balance(operations), 725.0)

    def test_calculate_expenses_by_category(self) -> None:
        operations = create_operations()

        self.assertEqual(
            calculate_expenses_by_category(operations),
            {
                "Food": 225.0,
                "Transport": 50.0,
            },
        )

    def test_filter_by_category_is_case_insensitive(self) -> None:
        operations = create_operations()

        result = filter_by_category(operations, "food")

        self.assertEqual(len(result), 2)
        self.assertTrue(
            all(operation.category == "Food" for operation in result),
        )

    def test_operation_validation(self) -> None:
        with self.assertRaises(ValueError):
            Operation(date(2026, 9, 1), "", 100.0, "income")

        with self.assertRaises(ValueError):
            Operation(date(2026, 9, 1), "Food", 0.0, "expense")


if __name__ == "__main__":
    main()
