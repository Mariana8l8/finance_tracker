"""CSV dataset generation for laboratory work 3."""

import csv
from pathlib import Path


FINANCE_STREAM_PATH = Path("data") / "finance_transactions_stream.csv"
DEFAULT_RECORD_COUNT = 120_000

CATEGORIES: tuple[str, ...] = (
    "Salary",
    "Food",
    "Transport",
    "Education",
    "Freelance",
    "Health",
)
TRANSACTION_TYPES: tuple[str, ...] = ("income", "expense")


def generate_finance_csv(
    path: Path,
    count: int,
) -> None:
    """Generate a deterministic CSV file with financial transactions."""

    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            [
                "transaction_id",
                "date",
                "type",
                "category",
                "amount",
                "description",
            ]
        )

        for transaction_id in range(1, count + 1):
            category = CATEGORIES[transaction_id % len(CATEGORIES)]
            transaction_type = "income" if category in {"Salary", "Freelance"} else "expense"
            amount = 100 + (transaction_id % 5000)
            writer.writerow(
                [
                    transaction_id,
                    f"2026-09-{transaction_id % 28 + 1:02d}",
                    transaction_type,
                    category,
                    f"{amount:.2f}",
                    f"Generated transaction {transaction_id}",
                ]
            )

        writer.writerow(["invalid", "bad-date", "expense", "", "-10", "Invalid row"])


def ensure_finance_csv(
    path: Path = FINANCE_STREAM_PATH,
    count: int = DEFAULT_RECORD_COUNT,
) -> Path:
    """Create the dataset when it does not exist yet."""

    if not path.exists():
        generate_finance_csv(path, count)

    return path
