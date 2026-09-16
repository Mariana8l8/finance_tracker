from __future__ import annotations

import json
from pathlib import Path

import pytest

from finance_tracker.exceptions import DataExportError
from finance_tracker.config import load_config
from finance_tracker.file_exporters import JsonTransactionExporter
from finance_tracker.file_pipeline import ImportStatistics, import_transactions
from finance_tracker.logging_config import configure_logging


def test_full_config_import_export_flow(tmp_path: Path) -> None:
    input_path = tmp_path / "transactions.csv"
    output_path = tmp_path / "out" / "transactions.json"
    log_path = tmp_path / "logs" / "app.log"
    config_path = tmp_path / "config.yaml"
    input_path.write_text(
        (
            "transaction_id,date,type,category,amount,description\n"
            "1,2026-09-12,income,Salary,1000.00,Salary\n"
            "2,2026-09-12,expense,Food,wrong,Bad amount\n"
            "3,2026-09-12,expense,Food,100.00,Lunch\n"
        ),
        encoding="utf-8",
    )
    config_path.write_text(
        (
            "input:\n"
            f"  path: {input_path}\n"
            "  format: csv\n"
            "output:\n"
            f"  path: {output_path}\n"
            "  format: json\n"
            "processing:\n"
            "  skip_invalid: true\n"
            "  minimum_amount: 0\n"
            "  allowed_types: income,expense\n"
            "logging:\n"
            "  level: INFO\n"
            f"  file: {log_path}\n"
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)
    configure_logging(config.logging.level, config.logging.file)
    statistics = ImportStatistics()
    records = import_transactions(
        config.input.path,
        allowed_types=config.processing.allowed_types,
        minimum_amount=config.processing.minimum_amount,
        skip_invalid=config.processing.skip_invalid,
        statistics=statistics,
    )
    exported = JsonTransactionExporter().export(records, config.output.path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert exported == 2
    assert statistics.total == 3
    assert statistics.invalid == 1
    assert [item["id"] for item in data] == [1, 3]
    assert log_path.exists()


def test_atomic_export_failure_keeps_previous_output(
    temporary_output: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import finance_tracker.file_exporters as exporters

    temporary_output.write_text("old valid data", encoding="utf-8")

    def broken_dump(*args: object, **kwargs: object) -> None:
        raise TypeError("serialization failed")

    monkeypatch.setattr(exporters.json, "dump", broken_dump)

    with pytest.raises(DataExportError, match="Cannot export"):
        JsonTransactionExporter().export(
            [
                {
                    "id": 1,
                    "date": "2026-09-12",
                    "type": "income",
                    "category": "Salary",
                    "amount": 10.0,
                    "description": "Salary",
                }
            ],
            temporary_output,
        )

    assert temporary_output.read_text(encoding="utf-8") == "old valid data"
    assert not temporary_output.with_suffix(".json.tmp").exists()


def test_repository_and_service_integration() -> None:
    from finance_tracker.domain import Budget, Category, Expense
    from finance_tracker.policies import CategoryLimitAlertPolicy
    from finance_tracker.repositories import InMemoryRepository
    from finance_tracker.value_objects import Money
    from datetime import date

    repository: InMemoryRepository[Budget] = InMemoryRepository()
    budget = Budget(id=1, name="September")
    food = Category("Food")
    budget.set_category_limit(food, Money(20.0))
    budget.add_transaction(
        Expense(
            id=1,
            occurred_on=date(2026, 9, 12),
            category=food,
            amount=Money(25.0),
            description="Lunch",
        )
    )
    repository.add(budget)

    assert repository.get(1) is budget
    assert CategoryLimitAlertPolicy().should_alert(repository.get(1), food)
