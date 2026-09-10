"""Console entry point for the finance tracker application."""

from datetime import date

from finance_tracker.models import Operation
from finance_tracker.services import (
    add_operation,
    calculate_balance,
    calculate_expenses,
    calculate_expenses_by_category,
    calculate_income,
    filter_by_category,
    sort_by_date,
)


def create_demo_operations() -> list[Operation]:
    """Create demo operations for application output."""

    operations: list[Operation] = []

    add_operation(
        operations,
        Operation(
            date=date(2026, 9, 1),
            category="Salary",
            amount=32000.00,
            operation_type="income",
        ),
    )
    add_operation(
        operations,
        Operation(
            date=date(2026, 9, 3),
            category="Food",
            amount=1850.50,
            operation_type="expense",
        ),
    )
    add_operation(
        operations,
        Operation(
            date=date(2026, 9, 5),
            category="Transport",
            amount=620.00,
            operation_type="expense",
        ),
    )
    add_operation(
        operations,
        Operation(
            date=date(2026, 9, 7),
            category="Freelance",
            amount=7600.00,
            operation_type="income",
        ),
    )
    add_operation(
        operations,
        Operation(
            date=date(2026, 9, 9),
            category="Food",
            amount=980.25,
            operation_type="expense",
        ),
    )

    return operations


def print_operations(
    operations: list[Operation],
    title: str,
) -> None:
    """Print operations as a table."""

    print(title)
    print(f"{'Date':12}{'Category':16}{'Type':10}{'Amount':>10}")
    print("-" * 48)

    for operation in operations:
        print(
            f"{operation.date.isoformat():12}"
            f"{operation.category:16}"
            f"{operation.operation_type:10}"
            f"{operation.amount:10.2f}"
        )


def print_expenses_by_category(
    expenses_by_category: dict[str, float],
) -> None:
    """Print expense totals grouped by category."""

    print("\nEXPENSES BY CATEGORY")
    print(f"{'Category':16}{'Amount':>10}")
    print("-" * 26)

    for category, amount in expenses_by_category.items():
        print(f"{category:16}{amount:10.2f}")


def main() -> None:
    """Run the demo console application."""

    operations = create_demo_operations()

    print_operations(
        sort_by_date(operations),
        "ALL OPERATIONS",
    )

    print()
    print(f"Total income:   {calculate_income(operations):10.2f}")
    print(f"Total expenses: {calculate_expenses(operations):10.2f}")
    print(f"Balance:        {calculate_balance(operations):10.2f}")

    print_expenses_by_category(
        calculate_expenses_by_category(operations),
    )

    food_operations = filter_by_category(
        operations,
        "Food",
    )
    print()
    print_operations(
        food_operations,
        "FOOD OPERATIONS",
    )


if __name__ == "__main__":
    main()

