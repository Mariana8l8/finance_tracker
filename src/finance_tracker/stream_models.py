"""Models for laboratory work 3 streaming task processing."""

from typing import NamedTuple


class TaskRecord(NamedTuple):
    """Validated project task record from the CSV stream."""

    task_id: int
    title: str
    assignee: str
    priority: str
    status: str


class PriorityIterator:
    """A small custom iterator over project priorities."""

    def __init__(
        self,
        priorities: tuple[str, ...],
    ) -> None:
        self._priorities = priorities
        self._index = 0

    def __iter__(self) -> "PriorityIterator":
        return self

    def __next__(self) -> str:
        if self._index >= len(self._priorities):
            raise StopIteration

        value = self._priorities[self._index]
        self._index += 1
        return value


class PriorityIterable:
    """Iterable that returns a fresh priority iterator each time."""

    def __init__(
        self,
        priorities: tuple[str, ...],
    ) -> None:
        self._priorities = priorities

    def __iter__(self) -> PriorityIterator:
        return PriorityIterator(self._priorities)

