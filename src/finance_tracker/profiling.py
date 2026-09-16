"""Profiling helpers for laboratory work 9."""

from __future__ import annotations

import cProfile
import io
import pstats
import tracemalloc
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from finance_tracker.performance import (
    FinancePerformanceStats,
    generate_performance_transactions,
    statistics_python,
)


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class MemoryProfile:
    """Memory profile result from tracemalloc."""

    current_mb: float
    peak_mb: float


def profile_baseline_statistics(
    dataset_size: int = 50_000,
    *,
    rows: int = 12,
) -> str:
    """Run cProfile for the baseline finance statistics calculation."""

    records = generate_performance_transactions(dataset_size)
    profiler = cProfile.Profile()
    profiler.enable()
    statistics_python(records)
    profiler.disable()

    output = io.StringIO()
    stats = pstats.Stats(profiler, stream=output)
    stats.sort_stats("cumulative")
    stats.print_stats(rows)
    return output.getvalue()


def measure_peak_memory(
    callback: Callable[[], T],
) -> tuple[T, MemoryProfile]:
    """Measure current and peak memory allocated by a callback."""

    tracemalloc.start()
    result = callback()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, MemoryProfile(
        current_mb=current / 1024 / 1024,
        peak_mb=peak / 1024 / 1024,
    )


def baseline_memory_profile(
    dataset_size: int = 50_000,
) -> tuple[FinancePerformanceStats, MemoryProfile]:
    """Measure memory for dataset generation and baseline statistics."""

    return measure_peak_memory(
        lambda: statistics_python(generate_performance_transactions(dataset_size))
    )
