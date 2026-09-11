"""Batch helpers for streaming finance pipelines."""

from collections.abc import Iterable, Iterator
from itertools import islice

from finance_tracker.stream_models import TransactionRecord


def batched_transactions(
    records: Iterable[TransactionRecord],
    batch_size: int,
) -> Iterator[list[TransactionRecord]]:
    """Yield lists of TransactionRecord objects with a selected batch size."""

    iterator = iter(records)

    while True:
        batch = list(
            islice(
                iterator,
                batch_size,
            )
        )
        if not batch:
            return

        yield batch

