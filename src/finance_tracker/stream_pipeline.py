"""Lazy pipeline assembly for laboratory work 3."""

from collections.abc import Iterator
from pathlib import Path

from finance_tracker.stream_filters import (
    filter_by_assignee,
    filter_by_priority,
    filter_by_status,
    normalize_tasks,
    validate_tasks,
)
from finance_tracker.stream_models import TaskRecord
from finance_tracker.stream_readers import parse_csv_rows, read_lines


def build_task_pipeline(
    path: Path,
    statuses: set[str] | None = None,
    priorities: set[str] | None = None,
    assignee: str | None = None,
) -> Iterator[TaskRecord]:
    """Build a lazy CSV processing pipeline for task records."""

    lines = read_lines(path)
    rows = parse_csv_rows(lines)
    valid = validate_tasks(rows)
    normalized = normalize_tasks(valid)

    current: Iterator[TaskRecord] = normalized

    if statuses is not None:
        current = filter_by_status(current, statuses)

    if priorities is not None:
        current = filter_by_priority(current, priorities)

    if assignee is not None:
        current = filter_by_assignee(current, assignee)

    return current

