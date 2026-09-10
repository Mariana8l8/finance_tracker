"""Console entry point for laboratory work 2."""

from finance_tracker.analytics import (
    build_summary,
    get_complexity_notes,
    rank_assignees_by_task_count,
    rank_priorities,
)
from finance_tracker.benchmark import benchmark_search
from finance_tracker.data import Task, tasks
from finance_tracker.processors import (
    build_recent_history,
    calculate_total_tasks,
    count_tasks_by_priority,
    count_tasks_by_status,
    create_status_filter,
    create_task_index,
    create_task_record,
    filter_tasks,
    get_unfinished_tasks,
    get_unique_assignees,
    group_tasks_by_assignee,
    group_tasks_by_assignee_and_status,
    sort_tasks_by_priority,
)


def print_tasks(
    title: str,
    items: list[Task],
) -> None:
    """Print task dictionaries as a table."""

    print(f"\n{title}")
    print(f"{'ID':>3}  {'Title':35} {'Assignee':16} {'Priority':8} {'Status':12}")
    print("-" * 84)

    for task in items:
        print(
            f"{int(task['id']):>3}  "
            f"{str(task['title'])[:35]:35} "
            f"{str(task['assignee'])[:16]:16} "
            f"{str(task['priority']):8} "
            f"{str(task['status']):12}"
        )


def print_counter(
    title: str,
    counter: dict[str, int],
) -> None:
    """Print Counter-like dictionaries."""

    print(f"\n{title}")
    for key, value in counter.items():
        print(f"{key:12} {value}")


def print_benchmark() -> None:
    """Print benchmark results."""

    print("\nBENCHMARK: LIST SEARCH VS DICT LOOKUP")
    print(f"{'Records':>10} {'List search':>14} {'Dict build':>14} {'Dict lookup':>14}")
    print("-" * 58)

    for result in benchmark_search():
        print(
            f"{int(result['records']):>10} "
            f"{result['list_search']:>14.8f} "
            f"{result['dict_build']:>14.8f} "
            f"{result['dict_lookup']:>14.8f}"
        )


def main() -> None:
    """Run the task data analysis demo."""

    print_tasks(
        "ALL PROJECT TASKS",
        tasks,
    )

    print("\nUnique assignees:", get_unique_assignees(tasks))
    print_counter("TASKS BY STATUS", count_tasks_by_status(tasks))
    print_counter("TASKS BY PRIORITY", count_tasks_by_priority(tasks))

    print_tasks(
        "UNFINISHED TASKS",
        get_unfinished_tasks(tasks),
    )

    grouped = group_tasks_by_assignee(tasks)
    print("\nGROUPED BY ASSIGNEE")
    for assignee, assigned_tasks in grouped.items():
        print(f"{assignee:16} {len(assigned_tasks)}")

    nested = group_tasks_by_assignee_and_status(tasks)
    print("\nNESTED GROUPING")
    for assignee, statuses in nested.items():
        compact = {
            status: len(status_tasks)
            for status, status_tasks in statuses.items()
        }
        print(f"{assignee:16} {compact}")

    index = create_task_index(tasks)
    print("\nSearch by ID:", index.get(4))

    is_active = create_status_filter("todo", "in_progress", "review")
    active_tasks = filter_tasks(tasks, is_active)
    print()
    print_tasks(
        "FILTERED BY CLOSURE",
        active_tasks,
    )

    print_tasks(
        "SORTED BY PRIORITY",
        sort_tasks_by_priority(tasks),
    )

    created_task = create_task_record(
        id=8,
        title="Created with kwargs",
        assignee="Oleh Koval",
        priority="medium",
        status="todo",
    )
    print("\nCreated via **kwargs:", created_task)
    print("Total via *args:", calculate_total_tasks(tasks, active_tasks))
    print("Recent history via deque:", list(build_recent_history(tasks)))
    print("Assignee rating:", rank_assignees_by_task_count(tasks))
    print("Priority rating:", rank_priorities(tasks))
    print("Summary:", build_summary(tasks))

    print("\nCOMPLEXITY NOTES")
    for operation, complexity in get_complexity_notes():
        print(f"{operation:30} {complexity}")

    print_benchmark()


if __name__ == "__main__":
    main()
