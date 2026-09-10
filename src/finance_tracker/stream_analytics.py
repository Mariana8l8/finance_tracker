"""Streaming analytics and experiments for task pipelines."""

from collections import Counter
from collections.abc import Iterable
from itertools import accumulate, count, groupby, islice, pairwise
from operator import attrgetter
from pathlib import Path
from time import perf_counter
import tracemalloc

from finance_tracker.stream_filters import UNFINISHED_STATUSES, validate_tasks
from finance_tracker.stream_models import TaskRecord
from finance_tracker.stream_pipeline import build_task_pipeline
from finance_tracker.stream_readers import parse_csv_rows, read_all_rows_eager, read_lines


def calculate_task_statistics(
    records: Iterable[TaskRecord],
) -> dict[str, object]:
    """Aggregate task statistics without materializing the whole stream."""

    total = 0
    status_counter: Counter[str] = Counter()
    priority_counter: Counter[str] = Counter()
    assignee_counter: Counter[str] = Counter()

    for record in records:
        total += 1
        status_counter[record.status] += 1
        priority_counter[record.priority] += 1
        assignee_counter[record.assignee] += 1

    return {
        "total": total,
        "status_counter": status_counter,
        "priority_counter": priority_counter,
        "assignee_counter": assignee_counter,
    }


def first_unfinished_tasks(
    records: Iterable[TaskRecord],
    limit: int,
) -> list[TaskRecord]:
    """Return the first N unfinished tasks using islice."""

    unfinished = (
        record
        for record in records
        if record.status in UNFINISHED_STATUSES
    )
    return list(islice(unfinished, limit))


def group_tasks_after_sorting(
    records: Iterable[TaskRecord],
) -> list[tuple[str, int]]:
    """Group tasks by assignee after sorting for itertools.groupby."""

    sorted_records = sorted(records, key=attrgetter("assignee"))
    return [
        (assignee, sum(1 for _ in group))
        for assignee, group in groupby(
            sorted_records,
            key=attrgetter("assignee"),
        )
    ]


def cumulative_done_counts(
    records: Iterable[TaskRecord],
    limit: int = 8,
) -> list[int]:
    """Use accumulate to count completed tasks cumulatively."""

    done_flags = (
        1 if record.status == "done" else 0
        for record in records
    )
    return list(
        islice(
            accumulate(done_flags),
            limit,
        )
    )


def pairwise_task_id_gaps(
    records: Iterable[TaskRecord],
    limit: int = 5,
) -> list[int]:
    """Use pairwise to calculate gaps between neighboring task IDs."""

    task_ids = (
        record.task_id
        for record in records
    )
    gaps = (
        current - previous
        for previous, current in pairwise(task_ids)
    )
    return list(islice(gaps, limit))


def infinite_task_numbers(
    limit: int,
) -> list[int]:
    """Demonstrate an infinite iterator safely limited by islice."""

    return list(islice(count(1), limit))


def measure_peak_memory(
    function,
    *args,
) -> tuple[object, int, float]:
    """Measure function result, peak memory and elapsed time."""

    tracemalloc.start()
    started = perf_counter()
    result = function(*args)
    elapsed = perf_counter() - started
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, peak, elapsed


def consume_eager(
    path: Path,
) -> int:
    """Eagerly read all rows, then validate them."""

    rows = read_all_rows_eager(path)
    return sum(1 for _ in validate_tasks(rows))


def consume_lazy(
    path: Path,
) -> int:
    """Consume the lazy validation pipeline."""

    rows = parse_csv_rows(read_lines(path))
    return sum(1 for _ in validate_tasks(rows))


def time_to_first_result(
    path: Path,
) -> float:
    """Measure how quickly the first valid unfinished high-priority task appears."""

    started = perf_counter()
    pipeline = build_task_pipeline(
        path,
        statuses={"todo", "in_progress", "review"},
        priorities={"high"},
    )
    next(pipeline, None)
    return perf_counter() - started


def run_eager_lazy_experiment(
    path: Path,
) -> dict[str, float]:
    """Compare eager and lazy processing for one dataset."""

    eager_count, eager_peak, eager_time = measure_peak_memory(
        consume_eager,
        path,
    )
    lazy_count, lazy_peak, lazy_time = measure_peak_memory(
        consume_lazy,
        path,
    )

    return {
        "eager_count": float(eager_count),
        "lazy_count": float(lazy_count),
        "eager_time": eager_time,
        "lazy_time": lazy_time,
        "eager_peak_mb": eager_peak / 1024 / 1024,
        "lazy_peak_mb": lazy_peak / 1024 / 1024,
        "time_to_first_result": time_to_first_result(path),
    }

