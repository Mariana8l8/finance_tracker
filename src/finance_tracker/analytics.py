"""Analytics functions for structured finance data."""

from collections import Counter, defaultdict

from finance_tracker.data import Transaction
from finance_tracker.decorators import measure_time
from finance_tracker.processors import (
    count_transactions_by_category,
    count_transactions_by_type,
    get_expense_transactions,
    get_unique_categories,
)


def calculate_total_by_type(
    items: list[Transaction],
    transaction_type: str,
) -> float:
    """Calculate total amount for a selected transaction type."""

    return sum(
        float(transaction["amount"])
        for transaction in items
        if transaction["type"] == transaction_type
    )


def calculate_expenses_by_category(
    items: list[Transaction],
) -> dict[str, float]:
    """Aggregate expenses by category."""

    result: defaultdict[str, float] = defaultdict(float)

    for transaction in get_expense_transactions(items):
        result[str(transaction["category"])] += float(transaction["amount"])

    return dict(result)


@measure_time("finance summary generation")
def build_summary(
    items: list[Transaction],
) -> dict[str, object]:
    """Build a compact summary for the finance dataset."""

    income = calculate_total_by_type(items, "income")
    expenses = calculate_total_by_type(items, "expense")

    return {
        "total_transactions": len(items),
        "unique_categories": len(get_unique_categories(items)),
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
        "type_counter": count_transactions_by_type(items),
        "category_counter": count_transactions_by_category(items),
    }


def rank_categories_by_expenses(
    items: list[Transaction],
) -> list[tuple[str, float]]:
    """Return expense categories ranked by total amount."""

    return sorted(
        calculate_expenses_by_category(items).items(),
        key=lambda item: item[1],
        reverse=True,
    )


def rank_categories_by_count(
    items: list[Transaction],
) -> list[tuple[str, int]]:
    """Return categories ranked by number of transactions."""

    counter = Counter(
        str(transaction["category"])
        for transaction in items
    )

    return counter.most_common()


def get_complexity_notes() -> list[tuple[str, str]]:
    """Return Big-O notes for the operations used in this lab."""

    return [
        ("Linear search in list", "O(n)"),
        ("Build dict index", "O(n)"),
        ("Average dict lookup by key", "O(1)"),
        ("Average set membership check", "O(1)"),
        ("Sorting transactions by amount", "O(n log n)"),
    ]

