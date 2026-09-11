from itertools import islice
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from finance_tracker.stream_analytics import (
    calculate_finance_statistics,
    cumulative_balance,
    first_expenses,
    infinite_transaction_numbers,
    pairwise_amount_changes,
    run_eager_lazy_experiment,
)
from finance_tracker.stream_batches import batched_transactions
from finance_tracker.stream_data import generate_finance_csv
from finance_tracker.stream_models import TransactionTypeIterable
from finance_tracker.stream_pipeline import build_finance_pipeline


class TestStreamPipeline(TestCase):
    def test_transaction_type_iterable_returns_fresh_iterators(self) -> None:
        transaction_types = TransactionTypeIterable(("income", "expense"))

        self.assertEqual(list(transaction_types), ["income", "expense"])
        self.assertEqual(list(transaction_types), ["income", "expense"])

    def test_pipeline_filters_and_statistics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "transactions.csv"
            generate_finance_csv(path, 20)

            pipeline = build_finance_pipeline(
                path,
                transaction_types={"expense"},
                minimum_amount=100.0,
            )
            filtered = list(pipeline)
            statistics = calculate_finance_statistics(build_finance_pipeline(path))

            self.assertTrue(filtered)
            self.assertTrue(all(transaction.transaction_type == "expense" for transaction in filtered))
            self.assertTrue(all(transaction.amount >= 100.0 for transaction in filtered))
            self.assertEqual(statistics["total"], 20)

    def test_islice_batching_and_generators(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "transactions.csv"
            generate_finance_csv(path, 15)
            pipeline = build_finance_pipeline(path)

            try:
                first_three = list(islice(pipeline, 3))
            finally:
                pipeline.close()

            batch = next(batched_transactions(build_finance_pipeline(path), 4))

            self.assertEqual(len(first_three), 3)
            self.assertEqual(len(batch), 4)
            self.assertEqual(infinite_transaction_numbers(5), [1, 2, 3, 4, 5])

    def test_itertools_helpers_and_experiment(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "transactions.csv"
            generate_finance_csv(path, 30)

            expenses = first_expenses(build_finance_pipeline(path), 3)
            balance = cumulative_balance(build_finance_pipeline(path), 5)
            changes = pairwise_amount_changes(build_finance_pipeline(path), 4)
            experiment = run_eager_lazy_experiment(path)

            self.assertEqual(len(expenses), 3)
            self.assertEqual(len(balance), 5)
            self.assertEqual(changes, [1.0, 1.0, 1.0, 1.0])
            self.assertEqual(experiment["eager_count"], 30.0)
            self.assertEqual(experiment["lazy_count"], 30.0)


if __name__ == "__main__":
    main()
