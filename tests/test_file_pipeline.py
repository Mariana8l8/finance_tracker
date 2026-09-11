import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from finance_tracker.config import load_config
from finance_tracker.exceptions import ConfigurationError, RecordValidationError
from finance_tracker.file_exporters import export_transactions_json
from finance_tracker.file_pipeline import ImportStatistics, import_transactions


class TestReliableFilePipeline(TestCase):
    def test_load_config_resolves_paths_and_validates(self) -> None:
        config = load_config(Path("config") / "lab5_config.yaml")

        self.assertEqual(config.input.format, "csv")
        self.assertEqual(config.output.format, "json")
        self.assertTrue(config.input.path.exists())
        self.assertIn("expense", config.processing.allowed_types)

    def test_missing_config_fails_fast(self) -> None:
        with self.assertRaises(ConfigurationError):
            load_config(Path("config") / "missing.yaml")

    def test_tolerant_import_skips_invalid_rows(self) -> None:
        statistics = ImportStatistics()
        records = list(
            import_transactions(
                Path("examples") / "lab5_transactions.csv",
                allowed_types=frozenset({"income", "expense"}),
                minimum_amount=0.0,
                skip_invalid=True,
                statistics=statistics,
            )
        )

        self.assertEqual(statistics.total, 7)
        self.assertEqual(statistics.valid, 4)
        self.assertEqual(statistics.invalid, 3)
        self.assertEqual([record["id"] for record in records], [1, 2, 5, 7])

    def test_strict_import_preserves_exception_cause(self) -> None:
        statistics = ImportStatistics()

        with self.assertRaises(RecordValidationError) as context:
            list(
                import_transactions(
                    Path("examples") / "lab5_transactions.csv",
                    allowed_types=frozenset({"income", "expense"}),
                    minimum_amount=0.0,
                    skip_invalid=False,
                    statistics=statistics,
                )
            )

        self.assertEqual(context.exception.line_number, 4)
        self.assertEqual(context.exception.field, "amount")
        self.assertIsInstance(context.exception.__cause__, ValueError)

    def test_atomic_json_export_writes_valid_output(self) -> None:
        records = [
            {
                "id": 1,
                "date": "2026-09-01",
                "type": "income",
                "category": "Salary",
                "amount": 1000.0,
                "description": "Salary",
            }
        ]

        with TemporaryDirectory() as directory:
            path = Path(directory) / "transactions.json"
            exported = export_transactions_json(records, path)

            self.assertEqual(exported, 1)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))[0]["id"], 1)
            self.assertFalse(path.with_suffix(".json.tmp").exists())
