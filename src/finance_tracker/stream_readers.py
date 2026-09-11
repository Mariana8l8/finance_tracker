"""Streaming readers and parsers for CSV finance data."""

import csv
from collections.abc import Iterable, Iterator
from pathlib import Path


def read_lines(
    path: Path,
) -> Iterator[str]:
    """Read a text file lazily line by line."""

    with path.open("r", encoding="utf-8", newline="") as file:
        yield from file


def parse_csv_rows(
    lines: Iterable[str],
) -> Iterator[dict[str, str]]:
    """Parse CSV rows lazily from an iterable of lines."""

    reader = csv.DictReader(lines)
    yield from reader


def read_all_rows_eager(
    path: Path,
) -> list[dict[str, str]]:
    """Read all CSV rows into memory for eager comparison."""

    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return list(reader)
