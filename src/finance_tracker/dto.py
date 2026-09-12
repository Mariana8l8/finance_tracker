"""TypedDict payloads for external finance data."""

from typing import Literal, NotRequired, TypedDict


class TransactionPayload(TypedDict):
    """External payload for creating a transaction."""

    id: int
    date: str
    type: Literal["income", "expense"]
    category: str
    amount: float
    description: NotRequired[str]
