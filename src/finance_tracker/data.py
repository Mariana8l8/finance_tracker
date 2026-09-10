"""Structured demo data for laboratory work 2."""

Task = dict[str, object]

PRIORITY_ORDER: tuple[str, ...] = ("high", "medium", "low")
ACTIVE_STATUSES: set[str] = {"todo", "in_progress", "review"}

tasks: list[Task] = [
    {
        "id": 1,
        "title": "Create project structure",
        "assignee": "Maryana Roman",
        "priority": "high",
        "status": "done",
    },
    {
        "id": 2,
        "title": "Implement finance operation model",
        "assignee": "Maryana Roman",
        "priority": "high",
        "status": "done",
    },
    {
        "id": 3,
        "title": "Prepare README documentation",
        "assignee": "Oleh Koval",
        "priority": "medium",
        "status": "review",
    },
    {
        "id": 4,
        "title": "Add unit tests",
        "assignee": "Iryna Bondar",
        "priority": "high",
        "status": "in_progress",
    },
    {
        "id": 5,
        "title": "Create benchmark dataset",
        "assignee": "Oleh Koval",
        "priority": "low",
        "status": "todo",
    },
    {
        "id": 6,
        "title": "Generate laboratory report",
        "assignee": "Maryana Roman",
        "priority": "medium",
        "status": "todo",
    },
    {
        "id": 7,
        "title": "Review project statistics",
        "assignee": "Iryna Bondar",
        "priority": "low",
        "status": "done",
    },
]

