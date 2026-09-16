"""Reliable JSON export for finance transactions."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol, TextIO

from finance_tracker.dto import TransactionPayload
from finance_tracker.exceptions import DataExportError


class TransactionExporter(Protocol):
    """Protocol for transaction exporters."""

    def export(
        self,
        transactions: Iterable[TransactionPayload],
        path: Path,
    ) -> int:
        """Export transactions and return exported row count."""


class JsonTransactionExporter:
    """Streaming JSON exporter with atomic replacement."""

    def export(
        self,
        transactions: Iterable[TransactionPayload],
        path: Path,
    ) -> int:
        return export_transactions_json(transactions, path)


def export_transactions_json(
    transactions: Iterable[TransactionPayload],
    path: Path,
) -> int:
    """Write transaction payloads as JSON using a temporary file first."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    count = 0

    try:
        with temporary.open("w", encoding="utf-8") as file:
            count = _write_json_array(transactions, file)
        temporary.replace(path)
    except (OSError, TypeError) as error:
        temporary.unlink(missing_ok=True)
        raise DataExportError(f"Cannot export transactions to {path}") from error

    return count


def _write_json_array(
    transactions: Iterable[TransactionPayload],
    file: TextIO,
) -> int:
    file.write("[\n")
    first = True
    count = 0
    for transaction in transactions:
        if not first:
            file.write(",\n")
        json.dump(transaction, file, ensure_ascii=False, indent=2)
        first = False
        count += 1
    file.write("\n]\n")
    return count
