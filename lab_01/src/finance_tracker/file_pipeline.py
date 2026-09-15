"""Streaming CSV import, validation and experiments for laboratory work 5."""

from __future__ import annotations

import csv
import logging
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from time import perf_counter
from typing import Literal, cast
import tracemalloc

from finance_tracker.dto import TransactionPayload
from finance_tracker.exceptions import DataImportError, RecordValidationError


logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: tuple[str, ...] = (
    "transaction_id",
    "date",
    "type",
    "category",
    "amount",
    "description",
)


@dataclass(slots=True)
class ImportStatistics:
    """Counters for reliable import modes."""

    total: int = 0
    valid: int = 0
    invalid: int = 0


@dataclass(frozen=True, slots=True)
class MemoryExperimentResult:
    """One eager-vs-streaming measurement row."""

    records: int
    eager_time: float
    streaming_time: float
    eager_peak_mb: float
    streaming_peak_mb: float


def read_csv_rows(
    path: Path,
) -> Iterator[tuple[int, dict[str, str]]]:
    """Stream CSV rows with physical file line numbers."""

    try:
        with path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None:
                raise DataImportError("CSV file does not contain a header.")
            missing = set(REQUIRED_COLUMNS) - set(reader.fieldnames)
            if missing:
                raise DataImportError(f"CSV file is missing columns: {sorted(missing)}")

            for line_number, row in enumerate(reader, start=2):
                yield line_number, dict(row)
    except OSError as error:
        raise DataImportError(f"Cannot read CSV file: {path}") from error


def import_transactions(
    path: Path,
    *,
    allowed_types: frozenset[str],
    minimum_amount: float,
    skip_invalid: bool,
    statistics: ImportStatistics,
) -> Iterator[TransactionPayload]:
    """Import valid transactions using strict or tolerant validation policy."""

    seen_ids: set[int] = set()
    for line_number, row in read_csv_rows(path):
        statistics.total += 1
        try:
            payload = parse_transaction_row(
                row,
                line_number=line_number,
                allowed_types=allowed_types,
                seen_ids=seen_ids,
            )
            if payload["amount"] < minimum_amount:
                raise RecordValidationError(
                    "Amount is lower than configured minimum.",
                    line_number=line_number,
                    field="amount",
                )
        except RecordValidationError as error:
            statistics.invalid += 1
            if skip_invalid:
                logger.warning("Invalid record skipped: %s", error)
                continue
            raise
        else:
            statistics.valid += 1
            yield payload


def parse_transaction_row(
    row: dict[str, str],
    *,
    line_number: int,
    allowed_types: frozenset[str],
    seen_ids: set[int],
) -> TransactionPayload:
    """Validate one CSV row and convert it to external transaction DTO."""

    transaction_id = _parse_positive_int(
        row,
        key="transaction_id",
        line_number=line_number,
    )
    if transaction_id in seen_ids:
        raise RecordValidationError(
            "Transaction ID must be unique.",
            line_number=line_number,
            field="transaction_id",
        )

    raw_transaction_type = _required(row, "type", line_number)
    if raw_transaction_type not in allowed_types:
        raise RecordValidationError(
            "Unsupported transaction type.",
            line_number=line_number,
            field="type",
        )
    transaction_type = cast(
        Literal["income", "expense"],
        raw_transaction_type,
    )

    transaction_date = _required(row, "date", line_number)
    try:
        date.fromisoformat(transaction_date)
    except ValueError as error:
        raise RecordValidationError(
            "Date must use ISO format YYYY-MM-DD.",
            line_number=line_number,
            field="date",
        ) from error

    category = _required(row, "category", line_number)
    description = _required(row, "description", line_number)
    amount = _parse_positive_float(row, key="amount", line_number=line_number)
    seen_ids.add(transaction_id)

    return {
        "id": transaction_id,
        "date": transaction_date,
        "type": transaction_type,
        "category": category,
        "amount": amount,
        "description": description,
    }


def compare_strict_tolerant(
    path: Path,
    *,
    allowed_types: frozenset[str],
    minimum_amount: float,
) -> dict[str, ImportStatistics]:
    """Run the same file through strict and tolerant processing policies."""

    strict_statistics = ImportStatistics()
    try:
        list(
            import_transactions(
                path,
                allowed_types=allowed_types,
                minimum_amount=minimum_amount,
                skip_invalid=False,
                statistics=strict_statistics,
            )
        )
    except RecordValidationError:
        pass

    tolerant_statistics = ImportStatistics()
    list(
        import_transactions(
            path,
            allowed_types=allowed_types,
            minimum_amount=minimum_amount,
            skip_invalid=True,
            statistics=tolerant_statistics,
        )
    )

    return {
        "strict": strict_statistics,
        "tolerant": tolerant_statistics,
    }


def generate_large_csv(
    path: Path,
    count: int,
) -> None:
    """Generate deterministic finance CSV data for memory experiments."""

    path.parent.mkdir(parents=True, exist_ok=True)
    categories = ("Salary", "Food", "Transport", "Education", "Freelance")

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(REQUIRED_COLUMNS)
        for transaction_id in range(1, count + 1):
            category = categories[transaction_id % len(categories)]
            transaction_type = "income" if category in {"Salary", "Freelance"} else "expense"
            writer.writerow(
                [
                    transaction_id,
                    f"2026-09-{transaction_id % 28 + 1:02d}",
                    transaction_type,
                    category,
                    f"{100 + transaction_id % 5000:.2f}",
                    f"Generated transaction {transaction_id}",
                ]
            )


def run_memory_experiment(
    base_dir: Path,
    record_counts: Iterable[int],
) -> list[MemoryExperimentResult]:
    """Compare eager CSV loading and streaming import memory usage."""

    results: list[MemoryExperimentResult] = []
    for records in record_counts:
        path = base_dir / f"lab5_memory_{records}.csv"
        if not path.exists():
            generate_large_csv(path, records)
        eager_count, eager_peak, eager_time = _measure(
            _consume_eager,
            path,
        )
        streaming_count, streaming_peak, streaming_time = _measure(
            _consume_streaming,
            path,
        )
        if eager_count != streaming_count:
            raise DataImportError("Eager and streaming import counts differ.")
        results.append(
            MemoryExperimentResult(
                records=records,
                eager_time=eager_time,
                streaming_time=streaming_time,
                eager_peak_mb=eager_peak / 1024 / 1024,
                streaming_peak_mb=streaming_peak / 1024 / 1024,
            )
        )
    return results


def _required(
    row: dict[str, str],
    key: str,
    line_number: int,
) -> str:
    try:
        value = row[key].strip()
    except KeyError as error:
        raise RecordValidationError(
            "Required field is missing.",
            line_number=line_number,
            field=key,
        ) from error
    if not value:
        raise RecordValidationError(
            "Required field is empty.",
            line_number=line_number,
            field=key,
        )
    return value


def _parse_positive_int(
    row: dict[str, str],
    *,
    key: str,
    line_number: int,
) -> int:
    text = _required(row, key, line_number)
    try:
        value = int(text)
    except ValueError as error:
        raise RecordValidationError(
            "Value must be an integer.",
            line_number=line_number,
            field=key,
        ) from error
    if value <= 0:
        raise RecordValidationError(
            "Value must be positive.",
            line_number=line_number,
            field=key,
        )
    return value


def _parse_positive_float(
    row: dict[str, str],
    *,
    key: str,
    line_number: int,
) -> float:
    text = _required(row, key, line_number)
    try:
        value = float(text)
    except ValueError as error:
        raise RecordValidationError(
            "Value must be numeric.",
            line_number=line_number,
            field=key,
        ) from error
    if value <= 0:
        raise RecordValidationError(
            "Value must be positive.",
            line_number=line_number,
            field=key,
        )
    return value


def _consume_eager(
    path: Path,
) -> int:
    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    seen_ids: set[int] = set()
    return sum(
        1
        for line_number, row in enumerate(rows, start=2)
        if parse_transaction_row(
            dict(row),
            line_number=line_number,
            allowed_types=frozenset({"income", "expense"}),
            seen_ids=seen_ids,
        )
    )


def _consume_streaming(
    path: Path,
) -> int:
    statistics = ImportStatistics()
    return sum(
        1
        for _ in import_transactions(
            path,
            allowed_types=frozenset({"income", "expense"}),
            minimum_amount=0.0,
            skip_invalid=False,
            statistics=statistics,
        )
    )


def _measure(
    function: Callable[[Path], int],
    path: Path,
) -> tuple[int, int, float]:
    tracemalloc.start()
    started = perf_counter()
    count = function(path)
    elapsed = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return count, peak, elapsed
