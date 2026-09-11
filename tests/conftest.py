from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from finance_tracker.database import create_sqlite_engine
from finance_tracker.db_models import Base
from finance_tracker.domain import Budget, Category, Expense
from finance_tracker.value_objects import Money


@pytest.fixture
def food_category() -> Category:
    return Category("Food")


@pytest.fixture
def budget_with_food_limit(food_category: Category) -> Budget:
    budget = Budget(id=1, name="Test budget")
    budget.set_category_limit(food_category, Money(100.0))
    return budget


@pytest.fixture
def transaction_csv_factory(
    tmp_path: Path,
) -> Callable[[str], Path]:
    def create_csv(body: str) -> Path:
        path = tmp_path / "transactions.csv"
        path.write_text(
            "transaction_id,date,type,category,amount,description\n" + body,
            encoding="utf-8",
        )
        return path

    return create_csv


@pytest.fixture
def temporary_output(
    tmp_path: Path,
) -> Iterator[Path]:
    output = tmp_path / "result.json"
    yield output
    output.with_suffix(".json.tmp").unlink(missing_ok=True)


@pytest.fixture
def expense_transaction(food_category: Category) -> Expense:
    from datetime import date

    return Expense(
        id=1,
        occurred_on=date(2026, 9, 12),
        category=food_category,
        amount=Money(25.5),
        description="Lunch",
    )


@pytest.fixture
def sqlite_engine(tmp_path: Path) -> Iterator[Engine]:
    database_path = tmp_path / "finance_tracker_test.db"
    engine = create_sqlite_engine(f"sqlite:///{database_path.as_posix()}")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(sqlite_engine: Engine) -> Iterator[Session]:
    TestSession = sessionmaker(
        bind=sqlite_engine,
        expire_on_commit=False,
        future=True,
    )
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
