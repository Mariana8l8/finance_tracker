"""Small context managers and helpers for reliable file operations."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
import logging
from time import perf_counter


logger = logging.getLogger(__name__)


@contextmanager
def logged_operation(
    operation: str,
) -> Iterator[None]:
    """Log operation lifecycle and preserve original exceptions."""

    logger.info("%s started", operation)
    started = perf_counter()
    try:
        yield
    except Exception:
        logger.exception("%s failed", operation)
        raise
    else:
        logger.info("%s finished in %.6f s", operation, perf_counter() - started)
