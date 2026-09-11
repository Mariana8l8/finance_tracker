"""Small DB-API examples with parameterized SQLite queries."""

from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3


def find_transactions_by_category_dbapi(
    database_path: Path,
    category_name: str,
) -> list[tuple[int, str, float, str]]:
    """Find transactions by category using DB-API and a parameterized query."""

    with closing(sqlite3.connect(database_path)) as connection:
        with closing(connection.cursor()) as cursor:
            cursor.execute(
                """
                SELECT
                    transactions.id,
                    transactions.transaction_type,
                    transactions.amount,
                    transactions.description
                FROM transactions
                JOIN categories
                    ON transactions.category_id = categories.id
                WHERE categories.name = ?
                ORDER BY transactions.id
                """,
                (category_name,),
            )
            return [
                (int(row[0]), str(row[1]), float(row[2]), str(row[3]))
                for row in cursor.fetchall()
            ]
