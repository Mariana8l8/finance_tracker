"""Benchmark script for laboratory work 9."""

from __future__ import annotations

import csv
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from statistics import mean

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from finance_tracker.performance import (
    BenchmarkMeasurement,
    FinancePerformanceStats,
    cached_period_report,
    clear_cached_period_reports,
    generate_performance_transactions,
    measure_time,
    statistics_process_pool,
    statistics_python,
    statistics_thread_pool,
)
from finance_tracker.profiling import measure_peak_memory


RESULTS_PATH = Path("benchmarks") / "results" / "lab09_benchmark_results.csv"


def run_benchmarks(
    *,
    dataset_sizes: Sequence[int] = (10_000, 100_000, 500_000),
    worker_counts: Sequence[int] = (1, 2, 4),
    repeats: int = 3,
) -> list[BenchmarkMeasurement]:
    """Run repeatable finance analytics benchmarks."""

    measurements: list[BenchmarkMeasurement] = []
    for dataset_size in dataset_sizes:
        records = generate_performance_transactions(dataset_size)
        baseline_times = measure_time(
            lambda: statistics_python(records),
            repeats=repeats,
        )
        _, baseline_memory = measure_peak_memory(lambda: statistics_python(records))
        baseline_mean = mean(baseline_times)
        measurements.append(
            BenchmarkMeasurement(
                dataset_size=dataset_size,
                method="Python loops",
                workers=1,
                run_times=baseline_times,
                mean_time=baseline_mean,
                peak_memory_mb=baseline_memory.peak_mb,
                speedup=1.0,
            )
        )

        for workers in worker_counts:
            measurements.append(
                _measure_method(
                    dataset_size=dataset_size,
                    method="ThreadPoolExecutor",
                    workers=workers,
                    baseline_mean=baseline_mean,
                    callback=lambda worker_count=workers: statistics_thread_pool(
                        records,
                        workers=worker_count,
                    ),
                    repeats=repeats,
                )
            )
            measurements.append(
                _measure_method(
                    dataset_size=dataset_size,
                    method="ProcessPoolExecutor",
                    workers=workers,
                    baseline_mean=baseline_mean,
                    callback=lambda worker_count=workers: statistics_process_pool(
                        records,
                        workers=worker_count,
                    ),
                    repeats=repeats,
                )
            )

        try:
            from finance_tracker.performance import statistics_numpy

            measurements.append(
                _measure_method(
                    dataset_size=dataset_size,
                    method="NumPy",
                    workers=None,
                    baseline_mean=baseline_mean,
                    callback=lambda: statistics_numpy(records),
                    repeats=repeats,
                )
            )
        except ModuleNotFoundError:
            pass

        clear_cached_period_reports()
        cached_period_report(dataset_size, "2026-01", "2026-12")
        measurements.append(
            _measure_method(
                dataset_size=dataset_size,
                method="Cached repeated report",
                workers=None,
                baseline_mean=baseline_mean,
                callback=lambda: cached_period_report(
                    dataset_size,
                    "2026-01",
                    "2026-12",
                ),
                repeats=repeats,
            )
        )

    return measurements


def write_csv(
    measurements: Sequence[BenchmarkMeasurement],
    path: Path = RESULTS_PATH,
) -> Path:
    """Save benchmark measurements as CSV."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(
            [
                "dataset_size",
                "method",
                "workers",
                "run_1",
                "run_2",
                "run_3",
                "mean_time",
                "peak_memory_mb",
                "speedup",
            ]
        )
        for measurement in measurements:
            runs = list(measurement.run_times[:3])
            while len(runs) < 3:
                runs.append(0.0)
            writer.writerow(
                [
                    measurement.dataset_size,
                    measurement.method,
                    measurement.workers if measurement.workers is not None else "",
                    *(f"{run_time:.6f}" for run_time in runs),
                    f"{measurement.mean_time:.6f}",
                    f"{measurement.peak_memory_mb:.6f}",
                    f"{measurement.speedup:.3f}",
                ]
            )
    return path


def _measure_method(
    *,
    dataset_size: int,
    method: str,
    workers: int | None,
    baseline_mean: float,
    callback: Callable[[], FinancePerformanceStats],
    repeats: int,
) -> BenchmarkMeasurement:
    run_times = measure_time(callback, repeats=repeats)
    _, memory = measure_peak_memory(callback)
    method_mean = mean(run_times)
    return BenchmarkMeasurement(
        dataset_size=dataset_size,
        method=method,
        workers=workers,
        run_times=run_times,
        mean_time=method_mean,
        peak_memory_mb=memory.peak_mb,
        speedup=baseline_mean / method_mean if method_mean else 0.0,
    )


def main() -> None:
    measurements = run_benchmarks()
    path = write_csv(measurements)
    print(path)


if __name__ == "__main__":
    main()
