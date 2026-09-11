"""Streaming analytics and experiments for finance pipelines."""

from collections import Counter
from collections.abc import Callable, Iterable
from itertools import accumulate, count, groupby, islice, pairwise
from operator import attrgetter
from pathlib import Path
from time import perf_counter
from typing import cast
import tracemalloc

from finance_tracker.stream_filters import validate_transactions
from finance_tracker.stream_models import TransactionRecord
from finance_tracker.stream_pipeline import build_finance_pipeline
from finance_tracker.stream_readers import parse_csv_rows, read_all_rows_eager, read_lines


def calculate_finance_statistics(
    records: Iterable[TransactionRecord],
) -> dict[str, object]:
    """Aggregate finance statistics without materializing the whole stream."""

    total = 0
    income = 0.0
    expenses = 0.0
    type_counter: Counter[str] = Counter()
    category_counter: Counter[str] = Counter()

    for record in records:
        total += 1
        type_counter[record.transaction_type] += 1
        category_counter[record.category] += 1

        if record.transaction_type == "income":
            income += record.amount
        else:
            expenses += record.amount

    return {
        "total": total,
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
        "type_counter": type_counter,
        "category_counter": category_counter,
    }


def first_expenses(
    records: Iterable[TransactionRecord],
    limit: int,
) -> list[TransactionRecord]:
    """Return the first N expenses using islice."""

    expenses = (
        record
        for record in records
        if record.transaction_type == "expense"
    )
    return list(islice(expenses, limit))


def group_transactions_after_sorting(
    records: Iterable[TransactionRecord],
) -> list[tuple[str, int]]:
    """Group transactions by category after sorting for itertools.groupby."""

    sorted_records = sorted(records, key=attrgetter("category"))
    return [
        (category, sum(1 for _ in group))
        for category, group in groupby(
            sorted_records,
            key=attrgetter("category"),
        )
    ]


def cumulative_balance(
    records: Iterable[TransactionRecord],
    limit: int = 8,
) -> list[float]:
    """Use accumulate to calculate running balance."""

    signed_amounts = (
        record.amount
        if record.transaction_type == "income"
        else -record.amount
        for record in records
    )
    return list(
        islice(
            accumulate(signed_amounts),
            limit,
        )
    )


def pairwise_amount_changes(
    records: Iterable[TransactionRecord],
    limit: int = 5,
) -> list[float]:
    """Use pairwise to calculate changes between neighboring amounts."""

    amounts = (
        record.amount
        for record in records
    )
    changes = (
        current - previous
        for previous, current in pairwise(amounts)
    )
    return list(islice(changes, limit))


def infinite_transaction_numbers(
    limit: int,
) -> list[int]:
    """Demonstrate an infinite iterator safely limited by islice."""

    return list(islice(count(1), limit))


def measure_peak_memory(
    function: Callable[..., object],
    *args: object,
) -> tuple[object, int, float]:
    """Measure function result, peak memory and elapsed time."""

    tracemalloc.start()
    started = perf_counter()
    result = function(*args)
    elapsed = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, peak, elapsed


def consume_eager(
    path: Path,
) -> int:
    """Eagerly read all rows, then validate them."""

    rows = read_all_rows_eager(path)
    return sum(1 for _ in validate_transactions(rows))


def consume_lazy(
    path: Path,
) -> int:
    """Consume the lazy validation pipeline."""

    rows = parse_csv_rows(read_lines(path))
    return sum(1 for _ in validate_transactions(rows))


def time_to_first_result(
    path: Path,
) -> float:
    """Measure how quickly the first valid large expense appears."""

    started = perf_counter()
    pipeline = build_finance_pipeline(
        path,
        transaction_types={"expense"},
        minimum_amount=1000.0,
    )
    next(pipeline, None)
    return perf_counter() - started


def run_eager_lazy_experiment(
    path: Path,
) -> dict[str, float]:
    """Compare eager and lazy processing for one dataset."""

    eager_count, eager_peak, eager_time = measure_peak_memory(
        consume_eager,
        path,
    )
    lazy_count, lazy_peak, lazy_time = measure_peak_memory(
        consume_lazy,
        path,
    )

    return {
        "eager_count": float(cast(int, eager_count)),
        "lazy_count": float(cast(int, lazy_count)),
        "eager_time": eager_time,
        "lazy_time": lazy_time,
        "eager_peak_mb": eager_peak / 1024 / 1024,
        "lazy_peak_mb": lazy_peak / 1024 / 1024,
        "time_to_first_result": time_to_first_result(path),
    }
