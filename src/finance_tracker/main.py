"""Console entry point for laboratory work 3."""

from itertools import chain, islice

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
from finance_tracker.stream_analytics import (
    calculate_task_statistics,
    cumulative_done_counts,
    first_unfinished_tasks,
    group_tasks_after_sorting,
    infinite_task_numbers,
    pairwise_task_id_gaps,
    run_eager_lazy_experiment,
)
from finance_tracker.stream_batches import batched_tasks
from finance_tracker.stream_data import DEFAULT_RECORD_COUNT, ensure_task_csv
from finance_tracker.stream_filters import UNFINISHED_STATUSES
from finance_tracker.stream_models import PriorityIterable, TaskRecord
from finance_tracker.stream_pipeline import build_task_pipeline


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


def print_stream_tasks(
    title: str,
    items: list[TaskRecord],
) -> None:
    """Print streamed task records as a compact table."""

    print(f"\n{title}")
    print(f"{'ID':>6}  {'Title':28} {'Assignee':16} {'Priority':8} {'Status':12}")
    print("-" * 78)

    for task in items:
        print(
            f"{task.task_id:>6}  "
            f"{task.title[:28]:28} "
            f"{task.assignee[:16]:16} "
            f"{task.priority:8} "
            f"{task.status:12}"
        )


def run_lab2_demo() -> None:
    """Run the task data analysis demo from laboratory work 2."""

    print("\n=== LAB 2 DATA ANALYSIS SNAPSHOT ===")
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


def run_lab3_demo() -> None:
    """Run the streaming pipeline demo from laboratory work 3."""

    print("\n=== LAB 3 STREAMING PIPELINE ===")
    path = ensure_task_csv(count=DEFAULT_RECORD_COUNT)
    print(f"Dataset: {path} ({DEFAULT_RECORD_COUNT} generated records + 1 invalid row)")

    priorities = PriorityIterable(("high", "medium", "low"))
    print("Custom iterator priorities:", list(priorities))
    print("Custom iterator reused:", list(priorities))

    pipeline = build_task_pipeline(
        path,
        statuses=UNFINISHED_STATUSES,
        priorities={"high"},
    )
    first_tasks = list(islice(pipeline, 5))
    print_stream_tasks("FIRST 5 UNFINISHED HIGH-PRIORITY TASKS", first_tasks)

    assignee_pipeline = build_task_pipeline(
        path,
        assignee="Maryana Roman",
    )
    print_stream_tasks(
        "LAZY ASSIGNEE FILTER",
        list(islice(assignee_pipeline, 3)),
    )

    chained = chain(
        build_task_pipeline(path, statuses={"todo"}),
        build_task_pipeline(path, statuses={"review"}),
    )
    print_stream_tasks(
        "CHAINED TODO + REVIEW STREAM",
        list(islice(chained, 4)),
    )

    batch_pipeline = build_task_pipeline(path, statuses=UNFINISHED_STATUSES)
    first_batch = next(batched_tasks(batch_pipeline, batch_size=4))
    print_stream_tasks("FIRST BATCH", first_batch)

    stats = calculate_task_statistics(build_task_pipeline(path))
    print("\nSTREAMING STATISTICS")
    print("Total valid records:", stats["total"])
    print("Status counter:", stats["status_counter"])
    print("Priority counter:", stats["priority_counter"])

    print("First unfinished:", first_unfinished_tasks(build_task_pipeline(path), 3))
    print("Grouped after sorting:", group_tasks_after_sorting(islice(build_task_pipeline(path), 30)))
    print("Cumulative done counts:", cumulative_done_counts(build_task_pipeline(path), 8))
    print("Pairwise task ID gaps:", pairwise_task_id_gaps(build_task_pipeline(path), 5))
    print("Infinite count limited by islice:", infinite_task_numbers(10))

    experiment = run_eager_lazy_experiment(path)
    print("\nEAGER VS LAZY EXPERIMENT")
    print(f"Eager count: {experiment['eager_count']:.0f}")
    print(f"Lazy count: {experiment['lazy_count']:.0f}")
    print(f"Eager time: {experiment['eager_time']:.6f} s")
    print(f"Lazy time: {experiment['lazy_time']:.6f} s")
    print(f"Eager peak memory: {experiment['eager_peak_mb']:.2f} MB")
    print(f"Lazy peak memory: {experiment['lazy_peak_mb']:.2f} MB")
    print(f"Time to first result: {experiment['time_to_first_result']:.6f} s")


def main() -> None:
    """Run the current laboratory demonstration."""

    run_lab3_demo()


if __name__ == "__main__":
    main()
