"""Decorators used by the structured data processing module."""

from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def measure_time(
    label: str | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Print execution time for the wrapped function."""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start = perf_counter()
            result = func(*args, **kwargs)
            elapsed = perf_counter() - start
            name = label or func.__name__
            print(f"{name}: {elapsed:.8f} s")
            return result

        return wrapper

    return decorator

