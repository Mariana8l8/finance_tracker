from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from finance_tracker.database import create_schema
from finance_tracker.db_models import BudgetRecord, CategoryRecord, TransactionRecordORM
from finance_tracker.db_repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from finance_tracker.db_services import transfer_between_budgets
from finance_tracker.dbapi import find_transactions_by_category_dbapi


def test_budget_repository_crud(db_session: Session) -> None:
    repository = BudgetRepository(db_session)

    budget = repository.add("September", "UAH")
    loaded = repository.get_by_id(budget.id)
    assert loaded is not None
    assert loaded.name == "September"

    updated = repository.update_name(budget.id, "September budget")
    deleted = repository.delete(budget.id)

    assert updated is not None
    assert updated.name == "September budget"
    assert deleted is True
    assert repository.get_by_id(budget.id) is None


def test_category_repository_enforces_foreign_key(db_session: Session) -> None:
    repository = CategoryRepository(db_session)

    with pytest.raises(IntegrityError):
        repository.add(999, "Food")


def test_transaction_repository_create_read_update_delete(db_session: Session) -> None:
    budget = BudgetRepository(db_session).add("Main")
    category = CategoryRepository(db_session).add(budget.id, "Food", 500.0)
    repository = TransactionRepository(db_session)

    transaction = repository.add(
        budget_id=budget.id,
        category_id=category.id,
        occurred_on=date(2026, 9, 12),
        transaction_type="expense",
        amount=100.0,
        description="Groceries",
    )
    updated = repository.update_amount(transaction.id, 125.5)
    found = repository.list_by_category(category.id)
    deleted = repository.delete(transaction.id)

    assert updated is not None
    assert updated.amount == pytest.approx(125.5)
    assert [item.id for item in found] == [transaction.id]
    assert deleted is True
    assert repository.get_by_id(transaction.id) is None


def test_transaction_repository_aggregates_and_group_by(db_session: Session) -> None:
    budget = BudgetRepository(db_session).add("Main")
    categories = CategoryRepository(db_session)
    salary = categories.add(budget.id, "Salary")
    food = categories.add(budget.id, "Food")
    repository = TransactionRepository(db_session)
    repository.add(
        budget_id=budget.id,
        category_id=salary.id,
        occurred_on=date(2026, 9, 1),
        transaction_type="income",
        amount=1000.0,
        description="Salary",
    )
    repository.add(
        budget_id=budget.id,
        category_id=food.id,
        occurred_on=date(2026, 9, 2),
        transaction_type="expense",
        amount=100.0,
        description="Lunch",
    )
    repository.add(
        budget_id=budget.id,
        category_id=food.id,
        occurred_on=date(2026, 9, 3),
        transaction_type="expense",
        amount=50.0,
        description="Coffee",
    )

    assert repository.total_by_type(budget.id, "income") == pytest.approx(1000.0)
    assert repository.balance(budget.id) == pytest.approx(850.0)
    assert repository.count_by_category(budget.id) == [("Food", 2), ("Salary", 1)]
    assert repository.largest_transaction(budget.id).description == "Salary"


def test_dbapi_parameterized_query_finds_transactions(
    sqlite_engine: Engine,
    tmp_path: Path,
) -> None:
    create_schema(sqlite_engine)
    database_path = tmp_path / "finance_tracker_test.db"

    from sqlalchemy.orm import sessionmaker

    TestSession = sessionmaker(
        bind=sqlite_engine,
        expire_on_commit=False,
        future=True,
    )
    with TestSession() as session:
        budget = BudgetRepository(session).add("Main")
        food = CategoryRepository(session).add(budget.id, "Food")
        TransactionRepository(session).add(
            budget_id=budget.id,
            category_id=food.id,
            occurred_on=date(2026, 9, 12),
            transaction_type="expense",
            amount=20.0,
            description="Lunch",
        )

    rows = find_transactions_by_category_dbapi(database_path, "Food")

    assert rows == [(1, "expense", 20.0, "Lunch")]


def test_transaction_transfer_commits_two_records(db_session: Session) -> None:
    budgets = BudgetRepository(db_session)
    categories = CategoryRepository(db_session)
    source = budgets.add("Cash")
    target = budgets.add("Card")
    source_category = categories.add(source.id, "Transfer out")
    target_category = categories.add(target.id, "Transfer in")

    expense, income = transfer_between_budgets(
        db_session,
        source_budget_id=source.id,
        target_budget_id=target.id,
        source_category_id=source_category.id,
        target_category_id=target_category.id,
        amount=250.0,
        occurred_on=date(2026, 9, 12),
        description="Move money to card",
    )

    transactions = TransactionRepository(db_session)
    assert expense.transaction_type == "expense"
    assert income.transaction_type == "income"
    assert transactions.balance(source.id) == pytest.approx(-250.0)
    assert transactions.balance(target.id) == pytest.approx(250.0)


def test_transaction_transfer_rolls_back_on_failure(db_session: Session) -> None:
    budgets = BudgetRepository(db_session)
    categories = CategoryRepository(db_session)
    source = budgets.add("Cash")
    target = budgets.add("Card")
    source_category = categories.add(source.id, "Transfer out")

    with pytest.raises(ValueError, match="Category was not found"):
        transfer_between_budgets(
            db_session,
            source_budget_id=source.id,
            target_budget_id=target.id,
            source_category_id=source_category.id,
            target_category_id=999,
            amount=250.0,
            occurred_on=date(2026, 9, 12),
            description="Broken transfer",
        )

    assert TransactionRepository(db_session).list_for_budget(source.id) == []


def test_sqlalchemy_relationships_are_configured(db_session: Session) -> None:
    budget = BudgetRecord(name="Relations", currency="UAH")
    category = CategoryRecord(name="Food", spending_limit_amount=100.0)
    transaction = TransactionRecordORM(
        occurred_on=date(2026, 9, 12),
        transaction_type="expense",
        amount=10.0,
        description="Lunch",
    )
    budget.categories.append(category)
    budget.transactions.append(transaction)
    category.transactions.append(transaction)
    db_session.add(budget)
    db_session.commit()

    assert budget.categories[0].name == "Food"
    assert budget.transactions[0].category.name == "Food"
