from itertools import islice
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from finance_tracker.stream_analytics import (
    calculate_task_statistics,
    cumulative_done_counts,
    first_unfinished_tasks,
    infinite_task_numbers,
    pairwise_task_id_gaps,
    run_eager_lazy_experiment,
)
from finance_tracker.stream_batches import batched_tasks
from finance_tracker.stream_data import generate_task_csv
from finance_tracker.stream_filters import UNFINISHED_STATUSES
from finance_tracker.stream_models import PriorityIterable
from finance_tracker.stream_pipeline import build_task_pipeline


class TestStreamPipeline(TestCase):
    def test_priority_iterable_returns_fresh_iterators(self) -> None:
        priorities = PriorityIterable(("high", "medium", "low"))

        self.assertEqual(list(priorities), ["high", "medium", "low"])
        self.assertEqual(list(priorities), ["high", "medium", "low"])

    def test_pipeline_filters_and_statistics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tasks.csv"
            generate_task_csv(path, 20)

            pipeline = build_task_pipeline(
                path,
                statuses=UNFINISHED_STATUSES,
                priorities={"high"},
            )
            filtered = list(pipeline)
            statistics = calculate_task_statistics(build_task_pipeline(path))

            self.assertTrue(filtered)
            self.assertTrue(all(task.priority == "high" for task in filtered))
            self.assertTrue(all(task.status in UNFINISHED_STATUSES for task in filtered))
            self.assertEqual(statistics["total"], 20)

    def test_islice_batching_and_generators(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tasks.csv"
            generate_task_csv(path, 15)
            pipeline = build_task_pipeline(path)

            try:
                first_three = list(islice(pipeline, 3))
            finally:
                pipeline.close()

            batch = next(batched_tasks(build_task_pipeline(path), 4))

            self.assertEqual(len(first_three), 3)
            self.assertEqual(len(batch), 4)
            self.assertEqual(infinite_task_numbers(5), [1, 2, 3, 4, 5])

    def test_itertools_helpers_and_experiment(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tasks.csv"
            generate_task_csv(path, 30)

            unfinished = first_unfinished_tasks(build_task_pipeline(path), 3)
            cumulative = cumulative_done_counts(build_task_pipeline(path), 5)
            gaps = pairwise_task_id_gaps(build_task_pipeline(path), 4)
            experiment = run_eager_lazy_experiment(path)

            self.assertEqual(len(unfinished), 3)
            self.assertEqual(len(cumulative), 5)
            self.assertEqual(gaps, [1, 1, 1, 1])
            self.assertEqual(experiment["eager_count"], 30.0)
            self.assertEqual(experiment["lazy_count"], 30.0)


if __name__ == "__main__":
    main()
