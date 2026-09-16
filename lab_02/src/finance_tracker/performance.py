"""Performance experiments for laboratory work 9."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from functools import lru_cache
from math import sqrt
from threading import Lock, Thread
from time import perf_counter
from typing import Any, NamedTuple


CATEGORIES: tuple[str, ...] = (
    "Salary",
    "Food",
    "Transport",
    "Education",
    "Freelance",
    "Health",
    "Entertainment",
    "Utilities",
)
MONTHS: tuple[str, ...] = tuple(f"2026-{month:02d}" for month in range(1, 13))


class PerformanceTransaction(NamedTuple):
    """Compact immutable transaction used in repeatable benchmarks."""

    month: str
    category: str
    amount: float
    transaction_type: str


@dataclass(frozen=True, slots=True)
class FinancePerformanceStats:
    """Aggregated finance statistics used to compare implementations."""

    count: int
    income: float
    expenses: float
    balance: float
    minimum: float
    maximum: float
    average: float
    standard_deviation: float
    category_totals: tuple[tuple[str, float], ...]
    monthly_totals: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class PartialFinanceStats:
    """Intermediate statistics that can be combined after parallel work."""

    count: int
    income: float
    expenses: float
    amount_sum: float
    amount_square_sum: float
    minimum: float
    maximum: float
    category_totals: tuple[tuple[str, float], ...]
    monthly_totals: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class BenchmarkMeasurement:
    """One benchmark row suitable for a report table."""

    dataset_size: int
    method: str
    workers: int | None
    run_times: tuple[float, ...]
    mean_time: float
    peak_memory_mb: float
    speedup: float


def generate_performance_transactions(
    count: int,
) -> list[PerformanceTransaction]:
    """Generate deterministic finance operations for performance experiments."""

    records: list[PerformanceTransaction] = []
    for index in range(count):
        category = CATEGORIES[index % len(CATEGORIES)]
        month = MONTHS[index % len(MONTHS)]
        transaction_type = "income" if category in {"Salary", "Freelance"} else "expense"
        amount = 75.0 + float((index * 37) % 9_500) + (index % 17) * 0.25
        records.append(
            PerformanceTransaction(
                month=month,
                category=category,
                amount=amount,
                transaction_type=transaction_type,
            )
        )
    return records


def statistics_python(
    records: Sequence[PerformanceTransaction],
) -> FinancePerformanceStats:
    """Baseline implementation using plain Python loops."""

    return _finish_statistics(_partial_statistics(records))


def statistics_thread_pool(
    records: Sequence[PerformanceTransaction],
    *,
    workers: int = 4,
) -> FinancePerformanceStats:
    """Calculate statistics with ThreadPoolExecutor."""

    chunks = _chunk_records(records, workers)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        partials = list(executor.map(_partial_statistics, chunks))
    return _finish_statistics(_combine_partials(partials))


def statistics_process_pool(
    records: Sequence[PerformanceTransaction],
    *,
    workers: int = 4,
) -> FinancePerformanceStats:
    """Calculate statistics with ProcessPoolExecutor for CPU-bound work."""

    chunks = _chunk_records(records, workers)
    with ProcessPoolExecutor(max_workers=workers) as executor:
        partials = list(executor.map(_partial_statistics, chunks))
    return _finish_statistics(_combine_partials(partials))


def statistics_numpy(
    records: Sequence[PerformanceTransaction],
) -> FinancePerformanceStats:
    """Calculate statistics with NumPy vectorization."""

    import numpy as np

    category_ids: Any = np.asarray(
        [CATEGORIES.index(record.category) for record in records],
        dtype=np.int16,
    )
    month_ids: Any = np.asarray(
        [MONTHS.index(record.month) for record in records],
        dtype=np.int16,
    )
    type_ids: Any = np.asarray(
        [1 if record.transaction_type == "income" else 0 for record in records],
        dtype=np.int8,
    )
    amounts: Any = np.asarray([record.amount for record in records], dtype=np.float64)

    income = float(amounts[type_ids == 1].sum())
    expenses = float(amounts[type_ids == 0].sum())
    category_totals = tuple(
        sorted(
            (category, float(amounts[category_ids == category_index].sum()))
            for category_index, category in enumerate(CATEGORIES)
            if bool(np.any(category_ids == category_index))
        )
    )
    monthly_totals = tuple(
        sorted(
            (month, float(amounts[month_ids == month_index].sum()))
            for month_index, month in enumerate(MONTHS)
            if bool(np.any(month_ids == month_index))
        )
    )

    return FinancePerformanceStats(
        count=len(records),
        income=income,
        expenses=expenses,
        balance=income - expenses,
        minimum=float(amounts.min()) if len(records) else 0.0,
        maximum=float(amounts.max()) if len(records) else 0.0,
        average=float(amounts.mean()) if len(records) else 0.0,
        standard_deviation=float(amounts.std()) if len(records) else 0.0,
        category_totals=category_totals,
        monthly_totals=monthly_totals,
    )


def count_processed_with_threads(
    records: Sequence[PerformanceTransaction],
    *,
    workers: int = 4,
) -> int:
    """Demonstrate Thread, shared state and Lock synchronization."""

    processed = 0
    lock = Lock()

    def worker(chunk: Sequence[PerformanceTransaction]) -> None:
        nonlocal processed
        local_count = len(chunk)
        with lock:
            processed += local_count

    threads = [Thread(target=worker, args=(chunk,)) for chunk in _chunk_records(records, workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    return processed


@lru_cache(maxsize=64)
def cached_period_report(
    dataset_size: int,
    start_month: str,
    end_month: str,
) -> FinancePerformanceStats:
    """Cache repeated reports for an unchanged generated period."""

    records = [
        record
        for record in generate_performance_transactions(dataset_size)
        if start_month <= record.month <= end_month
    ]
    return statistics_python(records)


def clear_cached_period_reports() -> None:
    """Clear the report cache when the underlying dataset changes."""

    cached_period_report.cache_clear()


def measure_time(
    callback: Callable[[], object],
    *,
    repeats: int = 5,
) -> tuple[float, ...]:
    """Measure execution time with perf_counter."""

    run_times: list[float] = []
    for _ in range(repeats):
        start = perf_counter()
        callback()
        run_times.append(perf_counter() - start)
    return tuple(run_times)


def compare_statistics(
    left: FinancePerformanceStats,
    right: FinancePerformanceStats,
    *,
    tolerance: float = 1e-6,
) -> bool:
    """Check that optimized statistics match the baseline."""

    numeric_fields = (
        "income",
        "expenses",
        "balance",
        "minimum",
        "maximum",
        "average",
        "standard_deviation",
    )
    if left.count != right.count:
        return False
    for field in numeric_fields:
        if abs(getattr(left, field) - getattr(right, field)) > tolerance:
            return False
    return _rounded_pairs(left.category_totals) == _rounded_pairs(
        right.category_totals
    ) and _rounded_pairs(left.monthly_totals) == _rounded_pairs(right.monthly_totals)


def _partial_statistics(
    records: Sequence[PerformanceTransaction],
) -> PartialFinanceStats:
    category_totals: defaultdict[str, float] = defaultdict(float)
    monthly_totals: defaultdict[str, float] = defaultdict(float)
    income = 0.0
    expenses = 0.0
    amount_sum = 0.0
    amount_square_sum = 0.0
    minimum = float("inf")
    maximum = 0.0

    for record in records:
        amount = record.amount
        if record.transaction_type == "income":
            income += amount
        else:
            expenses += amount
        category_totals[record.category] += amount
        monthly_totals[record.month] += amount
        amount_sum += amount
        amount_square_sum += amount * amount
        if amount < minimum:
            minimum = amount
        if amount > maximum:
            maximum = amount

    if not records:
        minimum = 0.0

    return PartialFinanceStats(
        count=len(records),
        income=income,
        expenses=expenses,
        amount_sum=amount_sum,
        amount_square_sum=amount_square_sum,
        minimum=minimum,
        maximum=maximum,
        category_totals=tuple(sorted(category_totals.items())),
        monthly_totals=tuple(sorted(monthly_totals.items())),
    )


def _combine_partials(
    partials: Iterable[PartialFinanceStats],
) -> PartialFinanceStats:
    category_totals: defaultdict[str, float] = defaultdict(float)
    monthly_totals: defaultdict[str, float] = defaultdict(float)
    count = 0
    income = 0.0
    expenses = 0.0
    amount_sum = 0.0
    amount_square_sum = 0.0
    minimum = float("inf")
    maximum = 0.0

    for partial in partials:
        count += partial.count
        income += partial.income
        expenses += partial.expenses
        amount_sum += partial.amount_sum
        amount_square_sum += partial.amount_square_sum
        minimum = min(minimum, partial.minimum)
        maximum = max(maximum, partial.maximum)
        for category, total in partial.category_totals:
            category_totals[category] += total
        for month, total in partial.monthly_totals:
            monthly_totals[month] += total

    if count == 0:
        minimum = 0.0

    return PartialFinanceStats(
        count=count,
        income=income,
        expenses=expenses,
        amount_sum=amount_sum,
        amount_square_sum=amount_square_sum,
        minimum=minimum,
        maximum=maximum,
        category_totals=tuple(sorted(category_totals.items())),
        monthly_totals=tuple(sorted(monthly_totals.items())),
    )


def _finish_statistics(
    partial: PartialFinanceStats,
) -> FinancePerformanceStats:
    average = partial.amount_sum / partial.count if partial.count else 0.0
    variance = (
        partial.amount_square_sum / partial.count - average * average if partial.count else 0.0
    )
    return FinancePerformanceStats(
        count=partial.count,
        income=partial.income,
        expenses=partial.expenses,
        balance=partial.income - partial.expenses,
        minimum=partial.minimum,
        maximum=partial.maximum,
        average=average,
        standard_deviation=sqrt(max(variance, 0.0)),
        category_totals=partial.category_totals,
        monthly_totals=partial.monthly_totals,
    )


def _chunk_records(
    records: Sequence[PerformanceTransaction],
    workers: int,
) -> list[Sequence[PerformanceTransaction]]:
    if workers <= 0:
        raise ValueError("workers must be greater than zero.")
    chunk_size = max(1, (len(records) + workers - 1) // workers)
    return [records[start : start + chunk_size] for start in range(0, len(records), chunk_size)]


def _rounded_pairs(
    pairs: tuple[tuple[str, float], ...],
) -> tuple[tuple[str, float], ...]:
    return tuple((key, round(value, 6)) for key, value in pairs)
