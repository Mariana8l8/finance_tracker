from collections import Counter, deque
from unittest import TestCase, main

from finance_tracker.analytics import (
    build_summary,
    get_complexity_notes,
    rank_assignees_by_task_count,
)
from finance_tracker.data import tasks
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
    sort_tasks_by_priority,
)


class TestTaskAnalysis(TestCase):
    def test_unique_assignees_and_counters(self) -> None:
        self.assertEqual(
            get_unique_assignees(tasks),
            {
                "Maryana Roman",
                "Oleh Koval",
                "Iryna Bondar",
            },
        )
        self.assertEqual(count_tasks_by_status(tasks)["done"], 3)
        self.assertEqual(
            count_tasks_by_priority(tasks),
            Counter(
                {
                    "high": 3,
                    "medium": 2,
                    "low": 2,
                }
            ),
        )

    def test_grouping_filtering_and_index(self) -> None:
        grouped = group_tasks_by_assignee(tasks)
        index = create_task_index(tasks)

        self.assertEqual(len(grouped["Maryana Roman"]), 3)
        self.assertEqual(index[4]["title"], "Add unit tests")
        self.assertEqual(len(get_unfinished_tasks(tasks)), 4)

    def test_closure_and_lambda_sorting(self) -> None:
        is_review_or_todo = create_status_filter("review", "todo")
        filtered = filter_tasks(tasks, is_review_or_todo)
        sorted_tasks = sort_tasks_by_priority(tasks)

        self.assertEqual(
            {task["status"] for task in filtered},
            {"review", "todo"},
        )
        self.assertEqual(sorted_tasks[0]["priority"], "high")

    def test_args_kwargs_deque_and_summary(self) -> None:
        todo = filter_tasks(tasks, create_status_filter("todo"))
        review = filter_tasks(tasks, create_status_filter("review"))
        record = create_task_record(
            id=100,
            title="Demo",
            assignee="Tester",
            priority="low",
            status="todo",
        )
        history = build_recent_history(tasks, limit=2)
        summary = build_summary(tasks)

        self.assertEqual(calculate_total_tasks(todo, review), 3)
        self.assertEqual(record["id"], 100)
        self.assertIsInstance(history, deque)
        self.assertEqual(
            list(history),
            [
                "Generate laboratory report",
                "Review project statistics",
            ],
        )
        self.assertEqual(summary["total_tasks"], 7)

    def test_ranking_and_complexity_notes(self) -> None:
        ranking = rank_assignees_by_task_count(tasks)
        notes = dict(get_complexity_notes())

        self.assertEqual(ranking[0], ("Maryana Roman", 3))
        self.assertEqual(notes["Linear search in list"], "O(n)")
        self.assertEqual(notes["Average dict lookup by key"], "O(1)")


if __name__ == "__main__":
    main()
