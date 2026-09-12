from __future__ import annotations

from pathlib import Path

import pytest

from finance_tracker.exceptions import DataImportError, RecordValidationError
from finance_tracker.file_pipeline import (
    ImportStatistics,
    import_transactions,
    parse_transaction_row,
    read_csv_rows,
)


def test_parse_transaction_row_returns_typed_payload() -> None:
    payload = parse_transaction_row(
        {
            "transaction_id": "1",
            "date": "2026-09-12",
            "type": "expense",
            "category": "Food",
            "amount": "25.50",
            "description": "Lunch",
        },
        line_number=2,
        allowed_types=frozenset({"income", "expense"}),
        seen_ids=set(),
    )

    assert payload["id"] == 1
    assert payload["amount"] == pytest.approx(25.5)


@pytest.mark.parametrize(
    ("row", "field"),
    [
        pytest.param({"transaction_id": "0"}, "transaction_id", id="zero-id"),
        pytest.param({"transaction_id": "abc"}, "transaction_id", id="bad-id"),
        pytest.param({"transaction_id": "1", "date": "bad-date"}, "date", id="bad-date"),
        pytest.param(
            {"transaction_id": "1", "date": "2026-09-12", "type": "transfer"},
            "type",
            id="unsupported-type",
        ),
    ],
)
def test_parse_transaction_row_rejects_invalid_fields(
    row: dict[str, str],
    field: str,
) -> None:
    valid = {
        "transaction_id": "1",
        "date": "2026-09-12",
        "type": "expense",
        "category": "Food",
        "amount": "25.50",
        "description": "Lunch",
    }
    valid.update(row)

    with pytest.raises(RecordValidationError) as exc_info:
        parse_transaction_row(
            valid,
            line_number=2,
            allowed_types=frozenset({"income", "expense"}),
            seen_ids=set(),
        )

    assert exc_info.value.field == field


def test_parse_transaction_row_preserves_exception_cause() -> None:
    with pytest.raises(RecordValidationError) as exc_info:
        parse_transaction_row(
            {
                "transaction_id": "1",
                "date": "2026-09-12",
                "type": "expense",
                "category": "Food",
                "amount": "not-number",
                "description": "Lunch",
            },
            line_number=2,
            allowed_types=frozenset({"income", "expense"}),
            seen_ids=set(),
        )

    assert exc_info.value.field == "amount"
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_import_transactions_filters_by_minimum_amount(
    transaction_csv_factory: object,
) -> None:
    create_csv = transaction_csv_factory
    assert callable(create_csv)
    path = create_csv(
        "1,2026-09-12,expense,Food,10.00,Small\n2,2026-09-12,expense,Food,100.00,Large\n"
    )
    statistics = ImportStatistics()

    records = list(
        import_transactions(
            path,
            allowed_types=frozenset({"income", "expense"}),
            minimum_amount=50.0,
            skip_invalid=True,
            statistics=statistics,
        )
    )

    assert [record["id"] for record in records] == [2]
    assert statistics.valid == 1
    assert statistics.invalid == 1


def test_read_csv_rows_reports_missing_columns(tmp_path: Path) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("transaction_id,date\n1,2026-09-12\n", encoding="utf-8")

    with pytest.raises(DataImportError, match="missing columns"):
        list(read_csv_rows(path))
