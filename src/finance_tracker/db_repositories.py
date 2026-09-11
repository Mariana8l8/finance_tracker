"""Repository Pattern implementations backed by SQLAlchemy."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from finance_tracker.db_models import BudgetRecord, CategoryRecord, TransactionRecordORM


class BudgetRepository:
    """CRUD repository for budgets."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        name: str,
        currency: str = "UAH",
    ) -> BudgetRecord:
        budget = BudgetRecord(name=name, currency=currency)
        self._session.add(budget)
        self._session.commit()
        self._session.refresh(budget)
        return budget

    def get_by_id(
        self,
        budget_id: int,
    ) -> BudgetRecord | None:
        return self._session.get(BudgetRecord, budget_id)

    def get_by_name(
        self,
        name: str,
    ) -> BudgetRecord | None:
        statement = select(BudgetRecord).where(BudgetRecord.name == name)
        return self._session.scalar(statement)

    def list_all(self) -> list[BudgetRecord]:
        return list(self._session.scalars(select(BudgetRecord)))

    def update_name(
        self,
        budget_id: int,
        name: str,
    ) -> BudgetRecord | None:
        budget = self.get_by_id(budget_id)
        if budget is None:
            return None
        budget.name = name
        self._session.commit()
        self._session.refresh(budget)
        return budget

    def delete(
        self,
        budget_id: int,
    ) -> bool:
        budget = self.get_by_id(budget_id)
        if budget is None:
            return False
        self._session.delete(budget)
        self._session.commit()
        return True


class CategoryRepository:
    """CRUD repository for budget categories."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        budget_id: int,
        name: str,
        spending_limit_amount: float | None = None,
    ) -> CategoryRecord:
        category = CategoryRecord(
            budget_id=budget_id,
            name=name,
            spending_limit_amount=spending_limit_amount,
        )
        self._session.add(category)
        self._session.commit()
        self._session.refresh(category)
        return category

    def get_by_id(
        self,
        category_id: int,
    ) -> CategoryRecord | None:
        return self._session.get(CategoryRecord, category_id)

    def find_by_name(
        self,
        budget_id: int,
        name: str,
    ) -> CategoryRecord | None:
        statement = select(CategoryRecord).where(
            CategoryRecord.budget_id == budget_id,
            CategoryRecord.name == name,
        )
        return self._session.scalar(statement)

    def list_for_budget(
        self,
        budget_id: int,
    ) -> list[CategoryRecord]:
        statement = select(CategoryRecord).where(CategoryRecord.budget_id == budget_id)
        return list(self._session.scalars(statement))

    def update_limit(
        self,
        category_id: int,
        spending_limit_amount: float | None,
    ) -> CategoryRecord | None:
        category = self.get_by_id(category_id)
        if category is None:
            return None
        category.spending_limit_amount = spending_limit_amount
        self._session.commit()
        self._session.refresh(category)
        return category

    def delete(
        self,
        category_id: int,
    ) -> bool:
        category = self.get_by_id(category_id)
        if category is None:
            return False
        self._session.delete(category)
        self._session.commit()
        return True


class TransactionRepository:
    """CRUD and reporting repository for transactions."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self._session = session

    def add(
        self,
        *,
        budget_id: int,
        category_id: int,
        occurred_on: date,
        transaction_type: str,
        amount: float,
        description: str,
        notes: str | None = None,
    ) -> TransactionRecordORM:
        transaction = TransactionRecordORM(
            budget_id=budget_id,
            category_id=category_id,
            occurred_on=occurred_on,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            notes=notes,
        )
        self._session.add(transaction)
        self._session.commit()
        self._session.refresh(transaction)
        return transaction

    def get_by_id(
        self,
        transaction_id: int,
    ) -> TransactionRecordORM | None:
        return self._session.get(TransactionRecordORM, transaction_id)

    def list_for_budget(
        self,
        budget_id: int,
    ) -> list[TransactionRecordORM]:
        statement = (
            select(TransactionRecordORM)
            .where(TransactionRecordORM.budget_id == budget_id)
            .order_by(TransactionRecordORM.occurred_on, TransactionRecordORM.id)
        )
        return list(self._session.scalars(statement))

    def list_by_category(
        self,
        category_id: int,
    ) -> list[TransactionRecordORM]:
        statement = select(TransactionRecordORM).where(
            TransactionRecordORM.category_id == category_id
        )
        return list(self._session.scalars(statement))

    def list_by_type(
        self,
        budget_id: int,
        transaction_type: str,
    ) -> list[TransactionRecordORM]:
        statement = select(TransactionRecordORM).where(
            TransactionRecordORM.budget_id == budget_id,
            TransactionRecordORM.transaction_type == transaction_type,
        )
        return list(self._session.scalars(statement))

    def update_amount(
        self,
        transaction_id: int,
        amount: float,
    ) -> TransactionRecordORM | None:
        transaction = self.get_by_id(transaction_id)
        if transaction is None:
            return None
        transaction.amount = amount
        self._session.commit()
        self._session.refresh(transaction)
        return transaction

    def update_description(
        self,
        transaction_id: int,
        description: str,
    ) -> TransactionRecordORM | None:
        transaction = self.get_by_id(transaction_id)
        if transaction is None:
            return None
        transaction.description = description
        self._session.commit()
        self._session.refresh(transaction)
        return transaction

    def delete(
        self,
        transaction_id: int,
    ) -> bool:
        transaction = self.get_by_id(transaction_id)
        if transaction is None:
            return False
        self._session.delete(transaction)
        self._session.commit()
        return True

    def total_by_type(
        self,
        budget_id: int,
        transaction_type: str,
    ) -> float:
        statement = select(func.coalesce(func.sum(TransactionRecordORM.amount), 0.0)).where(
            TransactionRecordORM.budget_id == budget_id,
            TransactionRecordORM.transaction_type == transaction_type,
        )
        return float(self._session.scalar(statement) or 0.0)

    def balance(
        self,
        budget_id: int,
    ) -> float:
        income = self.total_by_type(budget_id, "income")
        expenses = self.total_by_type(budget_id, "expense")
        return income - expenses

    def count_by_category(
        self,
        budget_id: int,
    ) -> list[tuple[str, int]]:
        statement: Select[tuple[str, int]] = (
            select(CategoryRecord.name, func.count(TransactionRecordORM.id))
            .join(TransactionRecordORM, CategoryRecord.id == TransactionRecordORM.category_id)
            .where(TransactionRecordORM.budget_id == budget_id)
            .group_by(CategoryRecord.name)
            .order_by(CategoryRecord.name)
        )
        return [
            (category_name, int(count))
            for category_name, count in self._session.execute(statement).all()
        ]

    def largest_transaction(
        self,
        budget_id: int,
    ) -> TransactionRecordORM | None:
        statement = (
            select(TransactionRecordORM)
            .where(TransactionRecordORM.budget_id == budget_id)
            .order_by(TransactionRecordORM.amount.desc())
            .limit(1)
        )
        return self._session.scalar(statement)
