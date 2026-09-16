"""Small benchmark helpers for list search and dictionary lookup."""

from time import perf_counter

from finance_tracker.data import Transaction
from finance_tracker.processors import create_transaction_index, find_transaction_linear


def generate_transactions(
    count: int,
) -> list[Transaction]:
    """Generate synthetic transactions for a search benchmark."""

    categories = ("Salary", "Food", "Transport", "Education", "Freelance")
    transaction_types = ("income", "expense")

    return [
        {
            "id": transaction_id,
            "date": "2026-09-01",
            "category": categories[transaction_id % len(categories)],
            "amount": float(100 + transaction_id % 5000),
            "type": transaction_types[transaction_id % len(transaction_types)],
            "description": f"Generated transaction {transaction_id}",
        }
        for transaction_id in range(1, count + 1)
    ]


def benchmark_search(
    sizes: tuple[int, ...] = (1_000, 10_000, 100_000),
) -> list[dict[str, float]]:
    """Compare list search with dictionary lookup."""

    results: list[dict[str, float]] = []

    for size in sizes:
        items = generate_transactions(size)
        target_id = size

        start = perf_counter()
        find_transaction_linear(items, target_id)
        list_time = perf_counter() - start

        index_start = perf_counter()
        index = create_transaction_index(items)
        index_build_time = perf_counter() - index_start

        lookup_start = perf_counter()
        index.get(target_id)
        dict_time = perf_counter() - lookup_start

        results.append(
            {
                "records": float(size),
                "list_search": list_time,
                "dict_build": index_build_time,
                "dict_lookup": dict_time,
            }
        )

    return results
