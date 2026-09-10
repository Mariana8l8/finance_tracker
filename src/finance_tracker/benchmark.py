"""Small benchmark helpers for list search and dictionary lookup."""

from time import perf_counter

from finance_tracker.data import Task
from finance_tracker.processors import create_task_index, find_task_linear


def generate_tasks(
    count: int,
) -> list[Task]:
    """Generate synthetic tasks for a search benchmark."""

    priorities = ("high", "medium", "low")
    statuses = ("todo", "in_progress", "review", "done")

    return [
        {
            "id": task_id,
            "title": f"Generated task {task_id}",
            "assignee": f"User {task_id % 10}",
            "priority": priorities[task_id % len(priorities)],
            "status": statuses[task_id % len(statuses)],
        }
        for task_id in range(1, count + 1)
    ]


def benchmark_search(
    sizes: tuple[int, ...] = (1_000, 10_000, 100_000),
) -> list[dict[str, float]]:
    """Compare list search with dictionary lookup."""

    results: list[dict[str, float]] = []

    for size in sizes:
        items = generate_tasks(size)
        target_id = size

        start = perf_counter()
        find_task_linear(items, target_id)
        list_time = perf_counter() - start

        index_start = perf_counter()
        index = create_task_index(items)
        index_build_time = perf_counter() - index_start

        lookup_start = perf_counter()
        index.get(target_id)
        dict_time = perf_counter() - lookup_start

        results.append(
            {
                "records": float(size),
                "list_search": list_time,
                "dict_build": index_build_time,
                "dict_lookup": dict_time,
            }
        )

    return results

