"""Console entry point for the finance tracker laboratory project."""

from itertools import chain, islice
import logging
from pathlib import Path
from datetime import date
from typing import cast

from finance_tracker.analytics import (
    build_summary,
    find_largest_expense,
    get_complexity_notes,
    rank_categories_by_count,
    rank_categories_by_expenses,
)
from finance_tracker.benchmark import benchmark_search
from finance_tracker.config import load_config
from finance_tracker.data import Transaction, transactions
from finance_tracker.database import SessionLocal, create_schema, engine
from finance_tracker.db_repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from finance_tracker.db_services import transfer_between_budgets
from finance_tracker.dbapi import find_transactions_by_category_dbapi
from finance_tracker.file_exporters import JsonTransactionExporter
from finance_tracker.file_pipeline import (
    ImportStatistics,
    compare_strict_tolerant,
    import_transactions,
)
from finance_tracker.file_utils import logged_operation
from finance_tracker.logging_config import configure_logging
from finance_tracker.processors import (
    build_recent_history,
    calculate_total_transactions,
    count_transactions_by_category,
    count_transactions_by_type,
    create_transaction_index,
    create_transaction_record,
    create_type_filter,
    filter_transactions,
    filter_transactions_by_amount,
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
from finance_tracker.domain import Budget, Category
from finance_tracker.oop_services import (
    ConsoleNotifier,
    FinanceTrackerService,
    JsonBudgetExporter,
)
from finance_tracker.policies import CategoryLimitAlertPolicy
from finance_tracker.protocols import BudgetExporter
from finance_tracker.repositories import InMemoryRepository
from finance_tracker.value_objects import Money


logger = logging.getLogger(__name__)


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
            f"{cast(int, transaction['id']):>3}  "
            f"{str(transaction['date']):12} "
            f"{str(transaction['category'])[:14]:14} "
            f"{str(transaction['type']):8} "
            f"{cast(float, transaction['amount']):10.2f}"
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
    income_transactions = filter_transactions(transactions, create_type_filter("income"))
    print_transactions(
        "FILTERED BY CLOSURE",
        expense_transactions,
    )

    print_transactions(
        "AMOUNT AT LEAST 2,000",
        filter_transactions_by_amount(transactions, threshold=2_000.0),
    )

    print("\nLargest expense:", find_largest_expense(transactions))

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
    print(
        "Total via *args:",
        calculate_total_transactions(income_transactions, expense_transactions),
    )
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
    print(
        "Grouped after sorting:",
        group_transactions_after_sorting(islice(build_finance_pipeline(path), 30)),
    )
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


def run_lab4_demo() -> None:
    """Run the professional OOP finance tracker demo from laboratory work 4."""

    print("\n=== LAB 4 OOP FINANCE TRACKER MODEL ===")
    repository: InMemoryRepository[Budget] = InMemoryRepository()
    exporter = JsonBudgetExporter()
    notifier = ConsoleNotifier()
    alert_policy = CategoryLimitAlertPolicy()

    print("Exporter matches protocol:", isinstance(exporter, BudgetExporter))

    service = FinanceTrackerService(
        budget_repository=repository,
        exporter=exporter,
        notifier=notifier,
        alert_policy=alert_policy,
    )

    budget = service.create_budget(
        budget_id=1,
        name="September budget",
    )
    food = Category("Food")
    budget.set_category_limit(
        food,
        Money(2_000.00),
    )

    service.add_transaction(
        budget_id=1,
        payload={
            "id": 1,
            "date": "2026-09-01",
            "type": "income",
            "category": "Salary",
            "amount": 32_000.00,
            "description": "Monthly salary",
        },
        recipient="maryana@example.com",
    )
    service.add_transaction(
        budget_id=1,
        payload={
            "id": 2,
            "date": "2026-09-03",
            "type": "expense",
            "category": "Food",
            "amount": 1_850.50,
            "description": "Groceries",
        },
        recipient="maryana@example.com",
    )
    service.add_transaction(
        budget_id=1,
        payload={
            "id": 3,
            "date": "2026-09-09",
            "type": "expense",
            "category": "Food",
            "amount": 980.25,
            "description": "Lunch and household items",
        },
        recipient="maryana@example.com",
    )

    print("Transactions:", len(budget))
    print("Transaction 2 exists:", 2 in budget)
    print("Transaction 2:", budget[2])
    print("Food spent:", budget.spent_by_category(food))
    print("Balance:", budget.balance)
    print("Export:", service.export_budget(1))


def run_lab5_demo() -> None:
    """Run the reliable import/export demo from laboratory work 5."""

    print("\n=== LAB 5 RELIABLE FINANCE IMPORT/EXPORT ===")
    config = load_config(Path("config") / "lab5_config.yaml")
    configure_logging(
        config.logging.level,
        config.logging.file,
    )

    statistics = ImportStatistics()
    exporter = JsonTransactionExporter()

    with logged_operation("Finance CSV import/export"):
        imported = import_transactions(
            config.input.path,
            allowed_types=config.processing.allowed_types,
            minimum_amount=config.processing.minimum_amount,
            skip_invalid=config.processing.skip_invalid,
            statistics=statistics,
        )
        exported = exporter.export(imported, config.output.path)

    policy_results = compare_strict_tolerant(
        config.input.path,
        allowed_types=config.processing.allowed_types,
        minimum_amount=config.processing.minimum_amount,
    )

    logger.info(
        "Total=%s, valid=%s, invalid=%s, exported=%s",
        statistics.total,
        statistics.valid,
        statistics.invalid,
        exported,
    )

    print(f"Config: {Path('config') / 'lab5_config.yaml'}")
    print(f"Input: {config.input.path}")
    print(f"Output: {config.output.path}")
    print(f"Log: {config.logging.file}")
    print(f"Total rows: {statistics.total}")
    print(f"Valid rows: {statistics.valid}")
    print(f"Invalid rows: {statistics.invalid}")
    print(f"Exported rows: {exported}")
    print("Strict mode before abort:", policy_results["strict"])
    print("Tolerant mode:", policy_results["tolerant"])


def run_lab7_demo() -> None:
    """Run the SQLite persistence demo from laboratory work 7."""

    print("\n=== LAB 7 SQLITE PERSISTENCE LAYER ===")
    create_schema(engine)

    with SessionLocal() as session:
        budgets = BudgetRepository(session)
        categories = CategoryRepository(session)
        transactions = TransactionRepository(session)

        main_budget = budgets.get_by_name("Main budget")
        if main_budget is None:
            main_budget = budgets.add("Main budget")
        card_budget = budgets.get_by_name("Card budget")
        if card_budget is None:
            card_budget = budgets.add("Card budget")

        salary = categories.find_by_name(main_budget.id, "Salary")
        if salary is None:
            salary = categories.add(main_budget.id, "Salary")
        food = categories.find_by_name(main_budget.id, "Food")
        if food is None:
            food = categories.add(main_budget.id, "Food", 2_000.0)
        transfer_out = categories.find_by_name(main_budget.id, "Transfer out")
        if transfer_out is None:
            transfer_out = categories.add(main_budget.id, "Transfer out")
        transfer_in = categories.find_by_name(card_budget.id, "Transfer in")
        if transfer_in is None:
            transfer_in = categories.add(card_budget.id, "Transfer in")

        if not transactions.list_for_budget(main_budget.id):
            transactions.add(
                budget_id=main_budget.id,
                category_id=salary.id,
                occurred_on=date(2026, 9, 1),
                transaction_type="income",
                amount=32_000.0,
                description="Monthly salary",
            )
            transactions.add(
                budget_id=main_budget.id,
                category_id=food.id,
                occurred_on=date(2026, 9, 3),
                transaction_type="expense",
                amount=1_850.5,
                description="Groceries",
            )

        if not transactions.list_for_budget(card_budget.id):
            transfer_between_budgets(
                session,
                source_budget_id=main_budget.id,
                target_budget_id=card_budget.id,
                source_category_id=transfer_out.id,
                target_category_id=transfer_in.id,
                amount=500.0,
                occurred_on=date(2026, 9, 12),
                description="Card top-up",
            )

        print("Budgets:", [budget.name for budget in budgets.list_all()])
        print("Main transactions:", len(transactions.list_for_budget(main_budget.id)))
        print("Main balance:", f"{transactions.balance(main_budget.id):.2f}")
        print("Category counts:", transactions.count_by_category(main_budget.id))
        print(
            "DB-API Food transactions:",
            find_transactions_by_category_dbapi(Path("data") / "finance_tracker.db", "Food"),
        )


def main() -> None:
    """Run the laboratory work 2 demonstration."""

    run_lab2_demo()


if __name__ == "__main__":
    main()
