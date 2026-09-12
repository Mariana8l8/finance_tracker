from collections import Counter, deque
from unittest import TestCase, main

from finance_tracker.analytics import (
    build_summary,
    calculate_expenses_by_category,
    rank_categories_by_expenses,
)
from finance_tracker.data import transactions
from finance_tracker.processors import (
    build_recent_history,
    calculate_total_transactions,
    count_transactions_by_category,
    count_transactions_by_type,
    create_transaction_index,
    create_transaction_record,
    create_type_filter,
    filter_transactions,
    get_expense_transactions,
    get_unique_categories,
    group_transactions_by_category,
    sort_transactions_by_amount,
)


class TestFinanceAnalysis(TestCase):
    def test_unique_categories_and_counters(self) -> None:
        self.assertEqual(
            get_unique_categories(transactions),
            {
                "Salary",
                "Food",
                "Transport",
                "Freelance",
                "Education",
                "Bonus",
            },
        )
        self.assertEqual(count_transactions_by_type(transactions)["expense"], 4)
        self.assertEqual(
            count_transactions_by_category(transactions),
            Counter(
                {
                    "Food": 2,
                    "Salary": 1,
                    "Transport": 1,
                    "Freelance": 1,
                    "Education": 1,
                    "Bonus": 1,
                }
            ),
        )

    def test_grouping_filtering_and_index(self) -> None:
        grouped = group_transactions_by_category(transactions)
        index = create_transaction_index(transactions)

        self.assertEqual(len(grouped["Food"]), 2)
        self.assertEqual(index[4]["category"], "Freelance")
        self.assertEqual(len(get_expense_transactions(transactions)), 4)

    def test_closure_and_lambda_sorting(self) -> None:
        is_expense = create_type_filter("expense")
        filtered = filter_transactions(transactions, is_expense)
        sorted_transactions = sort_transactions_by_amount(transactions)

        self.assertEqual(
            {transaction["type"] for transaction in filtered},
            {"expense"},
        )
        self.assertEqual(sorted_transactions[0]["amount"], 32000.00)

    def test_args_kwargs_deque_and_summary(self) -> None:
        income = filter_transactions(transactions, create_type_filter("income"))
        expenses = filter_transactions(transactions, create_type_filter("expense"))
        record = create_transaction_record(
            id=100,
            date="2026-09-20",
            category="Food",
            amount=150.0,
            type="expense",
            description="Demo",
        )
        history = build_recent_history(transactions, limit=2)
        summary = build_summary(transactions)

        self.assertEqual(calculate_total_transactions(income, expenses), 7)
        self.assertEqual(record["id"], 100)
        self.assertIsInstance(history, deque)
        self.assertEqual(
            list(history),
            [
                "Courses and books",
                "Project bonus",
            ],
        )
        self.assertEqual(summary["total_transactions"], 7)
        self.assertAlmostEqual(summary["balance"], 38549.25)

    def test_expense_ranking(self) -> None:
        expenses = calculate_expenses_by_category(transactions)
        ranking = rank_categories_by_expenses(transactions)

        self.assertEqual(expenses["Food"], 2830.75)
        self.assertEqual(ranking[0], ("Food", 2830.75))


if __name__ == "__main__":
    main()
