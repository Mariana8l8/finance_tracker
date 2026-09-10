"""CSV dataset generation for laboratory work 3."""

import csv
from pathlib import Path


TASK_STREAM_PATH = Path("data") / "tasks_stream.csv"
DEFAULT_RECORD_COUNT = 120_000

ASSIGNEES: tuple[str, ...] = (
    "Maryana Roman",
    "Oleh Koval",
    "Iryna Bondar",
    "Taras Novak",
    "Sofia Melnyk",
)
PRIORITIES: tuple[str, ...] = ("high", "medium", "low")
STATUSES: tuple[str, ...] = ("todo", "in_progress", "review", "done")


def generate_task_csv(
    path: Path,
    count: int,
) -> None:
    """Generate a deterministic CSV file with project tasks."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "task_id",
                "title",
                "assignee",
                "priority",
                "status",
            ]
        )

        for task_id in range(1, count + 1):
            writer.writerow(
                [
                    task_id,
                    f"Generated task {task_id}",
                    ASSIGNEES[task_id % len(ASSIGNEES)],
                    PRIORITIES[task_id % len(PRIORITIES)],
                    STATUSES[task_id % len(STATUSES)],
                ]
            )

        writer.writerow(["invalid", "", "", "urgent", "unknown"])


def ensure_task_csv(
    path: Path = TASK_STREAM_PATH,
    count: int = DEFAULT_RECORD_COUNT,
) -> Path:
    """Create the dataset when it does not exist yet."""

    if not path.exists():
        generate_task_csv(path, count)

    return path

