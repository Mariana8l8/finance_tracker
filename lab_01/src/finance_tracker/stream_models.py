"""Models for laboratory work 3 streaming finance processing."""

from typing import NamedTuple


class TransactionRecord(NamedTuple):
    """Validated financial transaction record from the CSV stream."""

    transaction_id: int
    date: str
    transaction_type: str
    category: str
    amount: float
    description: str


class TransactionTypeIterator:
    """A small custom iterator over transaction types."""

    def __init__(
        self,
        transaction_types: tuple[str, ...],
    ) -> None:
        self._transaction_types = transaction_types
        self._index = 0

    def __iter__(self) -> "TransactionTypeIterator":
        return self

    def __next__(self) -> str:
        if self._index >= len(self._transaction_types):
            raise StopIteration

        value = self._transaction_types[self._index]
        self._index += 1
        return value


class TransactionTypeIterable:
    """Iterable that returns a fresh transaction type iterator each time."""

    def __init__(
        self,
        transaction_types: tuple[str, ...],
    ) -> None:
        self._transaction_types = transaction_types

    def __iter__(self) -> TransactionTypeIterator:
        return TransactionTypeIterator(self._transaction_types)
