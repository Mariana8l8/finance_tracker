"""Processing functions for project task data."""

from collections import Counter, defaultdict, deque
from collections.abc import Callable

from finance_tracker.data import ACTIVE_STATUSES, PRIORITY_ORDER, Task


def get_unique_assignees(
    items: list[Task],
) -> set[str]:
    """Return a set of unique task assignees."""

    return {
        str(task["assignee"])
        for task in items
    }


def count_tasks_by_status(
    items: list[Task],
) -> Counter[str]:
    """Count tasks by status using Counter."""

    return Counter(
        str(task["status"])
        for task in items
    )


def count_tasks_by_priority(
    items: list[Task],
) -> Counter[str]:
    """Count tasks by priority using Counter."""

    return Counter(
        str(task["priority"])
        for task in items
    )


def get_unfinished_tasks(
    items: list[Task],
) -> list[Task]:
    """Return tasks that are not completed yet."""

    return [
        task
        for task in items
        if task["status"] in ACTIVE_STATUSES
    ]


def group_tasks_by_assignee(
    items: list[Task],
) -> dict[str, list[Task]]:
    """Group tasks by assignee using defaultdict."""

    grouped: defaultdict[str, list[Task]] = defaultdict(list)

    for task in items:
        grouped[str(task["assignee"])].append(task)

    return dict(grouped)


def group_tasks_by_assignee_and_status(
    items: list[Task],
) -> dict[str, dict[str, list[Task]]]:
    """Create nested grouping by assignee and status."""

    grouped: defaultdict[str, defaultdict[str, list[Task]]] = defaultdict(
        lambda: defaultdict(list),
    )

    for task in items:
        assignee = str(task["assignee"])
        status = str(task["status"])
        grouped[assignee][status].append(task)

    return {
        assignee: dict(statuses)
        for assignee, statuses in grouped.items()
    }


def create_task_index(
    items: list[Task],
) -> dict[int, Task]:
    """Create a dictionary index by task ID."""

    return {
        int(task["id"]): task
        for task in items
    }


def find_task_linear(
    items: list[Task],
    task_id: int,
) -> Task | None:
    """Find a task by ID using linear list search."""

    for task in items:
        if task["id"] == task_id:
            return task

    return None


def filter_tasks(
    items: list[Task],
    predicate: Callable[[Task], bool],
) -> list[Task]:
    """Filter tasks using a higher-order predicate function."""

    return [
        task
        for task in items
        if predicate(task)
    ]


def create_status_filter(
    *allowed_statuses: str,
) -> Callable[[Task], bool]:
    """Create a closure that filters tasks by selected statuses."""

    allowed = set(allowed_statuses)

    def predicate(task: Task) -> bool:
        return str(task["status"]) in allowed

    return predicate


def sort_tasks_by_priority(
    items: list[Task],
) -> list[Task]:
    """Sort tasks by priority using a lambda key."""

    priority_rank = {
        priority: index
        for index, priority in enumerate(PRIORITY_ORDER)
    }

    return sorted(
        items,
        key=lambda task: priority_rank.get(str(task["priority"]), 999),
    )


def calculate_total_tasks(
    *groups: list[Task],
) -> int:
    """Calculate a total number of tasks from several task groups."""

    return sum(len(group) for group in groups)


def create_task_record(
    **fields: object,
) -> Task:
    """Create a task dictionary from keyword arguments."""

    return dict(fields)


def build_recent_history(
    items: list[Task],
    limit: int = 3,
) -> deque[str]:
    """Return titles of the latest tasks using deque."""

    history: deque[str] = deque(maxlen=limit)

    for task in items:
        history.append(str(task["title"]))

    return history

