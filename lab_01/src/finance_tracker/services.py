"""Business logic for financial operations."""

from collections import defaultdict

from finance_tracker.models import Operation


def add_operation(
    operations: list[Operation],
    operation: Operation,
) -> None:
    """Add a new operation to the collection."""

    operations.append(operation)


def calculate_income(
    operations: list[Operation],
) -> float:
    """Calculate total income."""

    return sum(operation.amount for operation in operations if operation.operation_type == "income")


def calculate_expenses(
    operations: list[Operation],
) -> float:
    """Calculate total expenses."""

    return sum(
        operation.amount for operation in operations if operation.operation_type == "expense"
    )


def calculate_balance(
    operations: list[Operation],
) -> float:
    """Calculate current balance."""

    return calculate_income(operations) - calculate_expenses(operations)


def calculate_expenses_by_category(
    operations: list[Operation],
) -> dict[str, float]:
    """Group expenses by category."""

    result: defaultdict[str, float] = defaultdict(float)

    for operation in operations:
        if operation.operation_type == "expense":
            result[operation.category] += operation.amount

    return dict(result)


def filter_by_category(
    operations: list[Operation],
    category: str,
) -> list[Operation]:
    """Find all operations in a selected category."""

    normalized_category = category.casefold()
    return [
        operation
        for operation in operations
        if operation.category.casefold() == normalized_category
    ]


def sort_by_date(
    operations: list[Operation],
) -> list[Operation]:
    """Return operations sorted by date."""

    return sorted(operations, key=lambda operation: operation.date)
