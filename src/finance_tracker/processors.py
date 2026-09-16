"""Processing functions for structured finance data."""

from collections import Counter, defaultdict, deque
from collections.abc import Callable
from typing import cast

from finance_tracker.data import EXPENSE_TYPES, TRANSACTION_TYPES, Transaction


def get_unique_categories(
    items: list[Transaction],
) -> set[str]:
    """Return unique transaction categories."""

    return {str(transaction["category"]) for transaction in items}


def count_transactions_by_type(
    items: list[Transaction],
) -> Counter[str]:
    """Count transactions by income/expense type."""

    return Counter(str(transaction["type"]) for transaction in items)


def count_transactions_by_category(
    items: list[Transaction],
) -> Counter[str]:
    """Count transactions by category."""

    return Counter(str(transaction["category"]) for transaction in items)


def get_expense_transactions(
    items: list[Transaction],
) -> list[Transaction]:
    """Return expense transactions."""

    return [transaction for transaction in items if transaction["type"] in EXPENSE_TYPES]


def group_transactions_by_category(
    items: list[Transaction],
) -> dict[str, list[Transaction]]:
    """Group transactions by category using defaultdict."""

    grouped: defaultdict[str, list[Transaction]] = defaultdict(list)

    for transaction in items:
        grouped[str(transaction["category"])].append(transaction)

    return dict(grouped)


def group_transactions_by_type_and_category(
    items: list[Transaction],
) -> dict[str, dict[str, list[Transaction]]]:
    """Create nested grouping by type and category."""

    grouped: defaultdict[str, defaultdict[str, list[Transaction]]] = defaultdict(
        lambda: defaultdict(list),
    )

    for transaction in items:
        transaction_type = str(transaction["type"])
        category = str(transaction["category"])
        grouped[transaction_type][category].append(transaction)

    return {transaction_type: dict(categories) for transaction_type, categories in grouped.items()}


def create_transaction_index(
    items: list[Transaction],
) -> dict[int, Transaction]:
    """Create a dictionary index by transaction ID."""

    return {cast(int, transaction["id"]): transaction for transaction in items}


def find_transaction_linear(
    items: list[Transaction],
    transaction_id: int,
) -> Transaction | None:
    """Find a transaction by ID using linear list search."""

    for transaction in items:
        if transaction["id"] == transaction_id:
            return transaction

    return None


def filter_transactions(
    items: list[Transaction],
    predicate: Callable[[Transaction], bool],
) -> list[Transaction]:
    """Filter transactions using a higher-order predicate function."""

    return [transaction for transaction in items if predicate(transaction)]


def filter_transactions_by_amount(
    items: list[Transaction],
    threshold: float,
) -> list[Transaction]:
    """Return transactions whose amount is at least the given threshold."""

    return [
        transaction
        for transaction in items
        if cast(float, transaction["amount"]) >= threshold
    ]


def create_type_filter(
    *allowed_types: str,
) -> Callable[[Transaction], bool]:
    """Create a closure that filters transactions by type."""

    allowed = set(allowed_types)

    def predicate(transaction: Transaction) -> bool:
        return str(transaction["type"]) in allowed

    return predicate


def sort_transactions_by_amount(
    items: list[Transaction],
    reverse: bool = True,
) -> list[Transaction]:
    """Sort transactions by amount using a lambda key."""

    return sorted(
        items,
        key=lambda transaction: cast(float, transaction["amount"]),
        reverse=reverse,
    )


def sort_transactions_by_type(
    items: list[Transaction],
) -> list[Transaction]:
    """Sort transactions by the configured type order."""

    type_rank = {
        transaction_type: index for index, transaction_type in enumerate(TRANSACTION_TYPES)
    }

    return sorted(
        items,
        key=lambda transaction: type_rank.get(str(transaction["type"]), 999),
    )


def calculate_total_transactions(
    *groups: list[Transaction],
) -> int:
    """Calculate total number of transactions from several groups."""

    return sum(len(group) for group in groups)


def create_transaction_record(
    **fields: object,
) -> Transaction:
    """Create a transaction dictionary from keyword arguments."""

    return dict(fields)


def build_recent_history(
    items: list[Transaction],
    limit: int = 3,
) -> deque[str]:
    """Return descriptions of recent transactions using deque."""

    history: deque[str] = deque(maxlen=limit)

    for transaction in items:
        history.append(str(transaction["description"]))

    return history
