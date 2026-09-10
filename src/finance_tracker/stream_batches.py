"""Batch helpers for streaming task pipelines."""

from collections.abc import Iterable, Iterator
from itertools import islice

from finance_tracker.stream_models import TaskRecord


def batched_tasks(
    records: Iterable[TaskRecord],
    batch_size: int,
) -> Iterator[list[TaskRecord]]:
    """Yield lists of TaskRecord objects with a selected batch size."""

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

