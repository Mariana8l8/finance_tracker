"""Validation, filtering and transformation stages for task streams."""

from collections.abc import Iterable, Iterator

from finance_tracker.stream_models import TaskRecord

VALID_PRIORITIES = {"high", "medium", "low"}
VALID_STATUSES = {"todo", "in_progress", "review", "done"}
UNFINISHED_STATUSES = {"todo", "in_progress", "review"}


def validate_tasks(
    rows: Iterable[dict[str, str]],
) -> Iterator[TaskRecord]:
    """Validate raw CSV rows and yield TaskRecord objects."""

    for row in rows:
        try:
            task_id = int(row["task_id"])
            title = row["title"].strip()
            assignee = row["assignee"].strip()
            priority = row["priority"].strip()
            status = row["status"].strip()
        except (KeyError, TypeError, ValueError):
            continue

        if task_id <= 0:
            continue
        if not title or not assignee:
            continue
        if priority not in VALID_PRIORITIES:
            continue
        if status not in VALID_STATUSES:
            continue

        yield TaskRecord(
            task_id=task_id,
            title=title,
            assignee=assignee,
            priority=priority,
            status=status,
        )


def filter_by_status(
    records: Iterable[TaskRecord],
    allowed_statuses: set[str],
) -> Iterator[TaskRecord]:
    """Yield records with selected statuses."""

    for record in records:
        if record.status in allowed_statuses:
            yield record


def filter_by_priority(
    records: Iterable[TaskRecord],
    allowed_priorities: set[str],
) -> Iterator[TaskRecord]:
    """Yield records with selected priorities."""

    for record in records:
        if record.priority in allowed_priorities:
            yield record


def filter_by_assignee(
    records: Iterable[TaskRecord],
    assignee: str,
) -> Iterator[TaskRecord]:
    """Lazy assignee filter."""

    normalized = assignee.casefold()

    for record in records:
        if record.assignee.casefold() == normalized:
            yield record


def normalize_tasks(
    records: Iterable[TaskRecord],
) -> Iterator[TaskRecord]:
    """Normalize title and assignee text lazily."""

    for record in records:
        yield record._replace(
            title=record.title.strip().title(),
            assignee=record.assignee.strip(),
        )

