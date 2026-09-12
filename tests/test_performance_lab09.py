from __future__ import annotations

import pytest

from finance_tracker.performance import (
    cached_period_report,
    clear_cached_period_reports,
    compare_statistics,
    count_processed_with_threads,
    generate_performance_transactions,
    statistics_process_pool,
    statistics_python,
    statistics_thread_pool,
)
from finance_tracker.profiling import baseline_memory_profile, profile_baseline_statistics


def test_parallel_statistics_match_baseline() -> None:
    records = generate_performance_transactions(1_000)
    baseline = statistics_python(records)

    assert compare_statistics(
        baseline,
        statistics_thread_pool(records, workers=2),
    )
    assert compare_statistics(
        baseline,
        statistics_process_pool(records, workers=2),
    )


def test_numpy_statistics_match_baseline_when_available() -> None:
    pytest.importorskip("numpy")
    from finance_tracker.performance import statistics_numpy

    records = generate_performance_transactions(1_000)

    assert compare_statistics(
        statistics_python(records),
        statistics_numpy(records),
    )


def test_thread_lock_counts_processed_records() -> None:
    records = generate_performance_transactions(500)

    assert count_processed_with_threads(records, workers=4) == 500


def test_cached_period_report_reuses_second_call() -> None:
    clear_cached_period_reports()

    first = cached_period_report(2_000, "2026-01", "2026-06")
    second = cached_period_report(2_000, "2026-01", "2026-06")

    assert first == second
    assert cached_period_report.cache_info().hits == 1


def test_profiling_helpers_return_useful_output() -> None:
    profile = profile_baseline_statistics(1_000, rows=5)
    stats, memory = baseline_memory_profile(1_000)

    assert "statistics_python" in profile
    assert stats.count == 1_000
    assert memory.peak_mb > 0
