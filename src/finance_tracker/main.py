"""Console entry point for the finance tracker laboratory project."""

from itertools import chain, islice

from finance_tracker.analytics import (
    build_summary,
    get_complexity_notes,
    rank_categories_by_count,
    rank_categories_by_expenses,
)
from finance_tracker.benchmark import benchmark_search
from finance_tracker.data import Transaction, transactions
from finance_tracker.processors import (
    build_recent_history,
    calculate_total_transactions,
    count_transactions_by_category,
    count_transactions_by_type,
    create_transaction_index,
    create_transaction_record,
    create_type_filter,
    filter_transactions,
    get_expense_transactions,
    get_unique_categories,
    group_transactions_by_category,
    group_transactions_by_type_and_category,
    sort_transactions_by_amount,
)
from finance_tracker.stream_analytics import (
    calculate_finance_statistics,
    cumulative_balance,
    first_expenses,
    group_transactions_after_sorting,
    infinite_transaction_numbers,
    pairwise_amount_changes,
    run_eager_lazy_experiment,
)
from finance_tracker.stream_batches import batched_transactions
from finance_tracker.stream_data import DEFAULT_RECORD_COUNT, ensure_finance_csv
from finance_tracker.stream_models import TransactionRecord, TransactionTypeIterable
from finance_tracker.stream_pipeline import build_finance_pipeline


def print_transactions(
    title: str,
    items: list[Transaction],
) -> None:
    """Print transaction dictionaries as a table."""

    print(f"\n{title}")
    print(f"{'ID':>3}  {'Date':12} {'Category':14} {'Type':8} {'Amount':>10}")
    print("-" * 55)

    for transaction in items:
        print(
            f"{int(transaction['id']):>3}  "
            f"{str(transaction['date']):12} "
            f"{str(transaction['category'])[:14]:14} "
            f"{str(transaction['type']):8} "
            f"{float(transaction['amount']):10.2f}"
        )


def print_counter(
    title: str,
    counter: dict[str, int],
) -> None:
    """Print Counter-like dictionaries."""

    print(f"\n{title}")
    for key, value in counter.items():
        print(f"{key:14} {value}")


def print_benchmark() -> None:
    """Print benchmark results."""

    print("\nBENCHMARK: LIST SEARCH VS DICT LOOKUP")
    print(f"{'Records':>10} {'List search':>14} {'Dict build':>14} {'Dict lookup':>14}")
    print("-" * 58)

    for result in benchmark_search():
        print(
            f"{int(result['records']):>10} "
            f"{result['list_search']:>14.8f} "
            f"{result['dict_build']:>14.8f} "
            f"{result['dict_lookup']:>14.8f}"
        )


def print_stream_transactions(
    title: str,
    items: list[TransactionRecord],
) -> None:
    """Print streamed transaction records as a compact table."""

    print(f"\n{title}")
    print(f"{'ID':>6}  {'Date':12} {'Category':14} {'Type':8} {'Amount':>10}")
    print("-" * 60)

    for transaction in items:
        print(
            f"{transaction.transaction_id:>6}  "
            f"{transaction.date:12} "
            f"{transaction.category[:14]:14} "
            f"{transaction.transaction_type:8} "
            f"{transaction.amount:10.2f}"
        )


def run_lab2_demo() -> None:
    """Run the structured finance data analysis demo from laboratory work 2."""

    print("\n=== LAB 2 FINANCE DATA ANALYSIS SNAPSHOT ===")
    print_transactions(
        "ALL TRANSACTIONS",
        transactions,
    )

    print("\nUnique categories:", get_unique_categories(transactions))
    print_counter("TRANSACTIONS BY TYPE", count_transactions_by_type(transactions))
    print_counter("TRANSACTIONS BY CATEGORY", count_transactions_by_category(transactions))

    print_transactions(
        "EXPENSE TRANSACTIONS",
        get_expense_transactions(transactions),
    )

    grouped = group_transactions_by_category(transactions)
    print("\nGROUPED BY CATEGORY")
    for category, category_transactions in grouped.items():
        print(f"{category:14} {len(category_transactions)}")

    nested = group_transactions_by_type_and_category(transactions)
    print("\nNESTED GROUPING")
    for transaction_type, categories in nested.items():
        compact = {
            category: len(category_transactions)
            for category, category_transactions in categories.items()
        }
        print(f"{transaction_type:8} {compact}")

    index = create_transaction_index(transactions)
    print("\nSearch by ID:", index.get(4))

    is_expense = create_type_filter("expense")
    expense_transactions = filter_transactions(transactions, is_expense)
    print_transactions(
        "FILTERED BY CLOSURE",
        expense_transactions,
    )

    print_transactions(
        "SORTED BY AMOUNT",
        sort_transactions_by_amount(transactions),
    )

    created_transaction = create_transaction_record(
        id=8,
        date="2026-09-13",
        category="Food",
        amount=420.0,
        type="expense",
        description="Created with kwargs",
    )
    print("\nCreated via **kwargs:", created_transaction)
    print("Total via *args:", calculate_total_transactions(transactions, expense_transactions))
    print("Recent history via deque:", list(build_recent_history(transactions)))
    print("Expense category rating:", rank_categories_by_expenses(transactions))
    print("Category count rating:", rank_categories_by_count(transactions))
    print("Summary:", build_summary(transactions))

    print("\nCOMPLEXITY NOTES")
    for operation, complexity in get_complexity_notes():
        print(f"{operation:35} {complexity}")

    print_benchmark()


def run_lab3_demo() -> None:
    """Run the streaming finance pipeline demo from laboratory work 3."""

    print("\n=== LAB 3 FINANCE STREAMING PIPELINE ===")
    path = ensure_finance_csv(count=DEFAULT_RECORD_COUNT)
    print(f"Dataset: {path} ({DEFAULT_RECORD_COUNT} generated records + 1 invalid row)")

    transaction_types = TransactionTypeIterable(("income", "expense"))
    print("Custom iterator types:", list(transaction_types))
    print("Custom iterator reused:", list(transaction_types))

    pipeline = build_finance_pipeline(
        path,
        transaction_types={"expense"},
        minimum_amount=1000.0,
    )
    first_large_expenses = list(islice(pipeline, 5))
    print_stream_transactions("FIRST 5 LARGE EXPENSES", first_large_expenses)

    category_pipeline = build_finance_pipeline(
        path,
        category="Food",
    )
    print_stream_transactions(
        "LAZY CATEGORY FILTER",
        list(islice(category_pipeline, 3)),
    )

    chained = chain(
        build_finance_pipeline(path, transaction_types={"income"}),
        build_finance_pipeline(path, transaction_types={"expense"}),
    )
    print_stream_transactions(
        "CHAINED INCOME + EXPENSE STREAM",
        list(islice(chained, 4)),
    )

    batch_pipeline = build_finance_pipeline(path, transaction_types={"expense"})
    first_batch = next(batched_transactions(batch_pipeline, batch_size=4))
    print_stream_transactions("FIRST EXPENSE BATCH", first_batch)

    stats = calculate_finance_statistics(build_finance_pipeline(path))
    print("\nSTREAMING STATISTICS")
    print("Total valid records:", stats["total"])
    print("Income:", f"{stats['income']:.2f}")
    print("Expenses:", f"{stats['expenses']:.2f}")
    print("Balance:", f"{stats['balance']:.2f}")
    print("Type counter:", stats["type_counter"])
    print("Category counter:", stats["category_counter"])

    print("First expenses:", first_expenses(build_finance_pipeline(path), 3))
    print("Grouped after sorting:", group_transactions_after_sorting(islice(build_finance_pipeline(path), 30)))
    print("Cumulative balance:", cumulative_balance(build_finance_pipeline(path), 8))
    print("Pairwise amount changes:", pairwise_amount_changes(build_finance_pipeline(path), 5))
    print("Infinite count limited by islice:", infinite_transaction_numbers(10))

    experiment = run_eager_lazy_experiment(path)
    print("\nEAGER VS LAZY EXPERIMENT")
    print(f"Eager count: {experiment['eager_count']:.0f}")
    print(f"Lazy count: {experiment['lazy_count']:.0f}")
    print(f"Eager time: {experiment['eager_time']:.6f} s")
    print(f"Lazy time: {experiment['lazy_time']:.6f} s")
    print(f"Eager peak memory: {experiment['eager_peak_mb']:.2f} MB")
    print(f"Lazy peak memory: {experiment['lazy_peak_mb']:.2f} MB")
    print(f"Time to first result: {experiment['time_to_first_result']:.6f} s")


def main() -> None:
    """Run the current laboratory demonstration."""

    run_lab3_demo()


if __name__ == "__main__":
    main()

