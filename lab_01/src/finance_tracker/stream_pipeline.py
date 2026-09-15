"""Lazy pipeline assembly for laboratory work 3."""

from collections.abc import Iterator
from pathlib import Path

from finance_tracker.stream_filters import (
    filter_by_amount_threshold,
    filter_by_category,
    filter_by_type,
    normalize_transactions,
    validate_transactions,
)
from finance_tracker.stream_models import TransactionRecord
from finance_tracker.stream_readers import parse_csv_rows, read_lines


def build_finance_pipeline(
    path: Path,
    transaction_types: set[str] | None = None,
    category: str | None = None,
    minimum_amount: float | None = None,
) -> Iterator[TransactionRecord]:
    """Build a lazy CSV processing pipeline for finance records."""

    lines = read_lines(path)
    rows = parse_csv_rows(lines)
    valid = validate_transactions(rows)
    normalized = normalize_transactions(valid)

    current: Iterator[TransactionRecord] = normalized

    if transaction_types is not None:
        current = filter_by_type(current, transaction_types)

    if category is not None:
        current = filter_by_category(current, category)

    if minimum_amount is not None:
        current = filter_by_amount_threshold(current, minimum_amount)

    return current
