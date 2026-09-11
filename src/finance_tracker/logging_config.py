"""Logging setup for the reliable import/export pipeline."""

from __future__ import annotations

import logging
from pathlib import Path


def configure_logging(
    level_name: str,
    log_path: Path,
) -> None:
    """Configure file and console logging without duplicating handlers."""

    level = getattr(logging, level_name.upper(), None)
    if not isinstance(level, int):
        level = logging.INFO

    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))

    root.setLevel(level)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)
