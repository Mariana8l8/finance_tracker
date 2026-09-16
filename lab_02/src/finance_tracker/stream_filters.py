"""Validation, filtering and transformation stages for finance streams."""

from collections.abc import Iterable, Iterator

from finance_tracker.stream_models import TransactionRecord

VALID_TYPES = {"income", "expense"}


def validate_transactions(
    rows: Iterable[dict[str, str]],
) -> Iterator[TransactionRecord]:
    """Validate raw CSV rows and yield TransactionRecord objects."""

    for row in rows:
        try:
            transaction_id = int(row["transaction_id"])
            date = row["date"].strip()
            transaction_type = row["type"].strip()
            category = row["category"].strip()
            amount = float(row["amount"])
            description = row["description"].strip()
        except (KeyError, TypeError, ValueError):
            continue

        if transaction_id <= 0:
            continue
        if not date or not category or not description:
            continue
        if transaction_type not in VALID_TYPES:
            continue
        if amount <= 0:
            continue

        yield TransactionRecord(
            transaction_id=transaction_id,
            date=date,
            transaction_type=transaction_type,
            category=category,
            amount=amount,
            description=description,
        )


def filter_by_type(
    records: Iterable[TransactionRecord],
    allowed_types: set[str],
) -> Iterator[TransactionRecord]:
    """Yield records with selected transaction types."""

    for record in records:
        if record.transaction_type in allowed_types:
            yield record


def filter_by_category(
    records: Iterable[TransactionRecord],
    category: str,
) -> Iterator[TransactionRecord]:
    """Lazy category filter."""

    normalized = category.casefold()

    for record in records:
        if record.category.casefold() == normalized:
            yield record


def filter_by_amount_threshold(
    records: Iterable[TransactionRecord],
    minimum_amount: float,
) -> Iterator[TransactionRecord]:
    """Yield transactions with amount greater than or equal to threshold."""

    for record in records:
        if record.amount >= minimum_amount:
            yield record


def normalize_transactions(
    records: Iterable[TransactionRecord],
) -> Iterator[TransactionRecord]:
    """Normalize category and description text lazily."""

    for record in records:
        yield record._replace(
            category=record.category.strip().title(),
            description=record.description.strip(),
        )
