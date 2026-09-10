"""Analytics functions for project task data."""

from collections import Counter

from finance_tracker.data import Task
from finance_tracker.decorators import measure_time
from finance_tracker.processors import (
    count_tasks_by_priority,
    count_tasks_by_status,
    get_unfinished_tasks,
    get_unique_assignees,
)


@measure_time("summary generation")
def build_summary(
    items: list[Task],
) -> dict[str, object]:
    """Build a compact summary for the project task dataset."""

    status_counter = count_tasks_by_status(items)
    priority_counter = count_tasks_by_priority(items)

    return {
        "total_tasks": len(items),
        "unique_assignees": len(get_unique_assignees(items)),
        "unfinished_tasks": len(get_unfinished_tasks(items)),
        "status_counter": status_counter,
        "priority_counter": priority_counter,
    }


def rank_assignees_by_task_count(
    items: list[Task],
) -> list[tuple[str, int]]:
    """Return assignees ranked by number of assigned tasks."""

    counter = Counter(
        str(task["assignee"])
        for task in items
    )

    return counter.most_common()


def rank_priorities(
    items: list[Task],
) -> list[tuple[str, int]]:
    """Return priorities ranked by task count."""

    return count_tasks_by_priority(items).most_common()


def get_complexity_notes() -> list[tuple[str, str]]:
    """Return Big-O notes for the operations used in this lab."""

    return [
        ("Linear search in list", "O(n)"),
        ("Build dict index", "O(n)"),
        ("Average dict lookup by key", "O(1)"),
        ("Average set membership check", "O(1)"),
        ("Sorting tasks by priority", "O(n log n)"),
    ]

