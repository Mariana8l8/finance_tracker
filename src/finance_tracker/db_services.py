"""Transactional persistence services for finance tracker data."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from finance_tracker.db_models import BudgetRecord, CategoryRecord, TransactionRecordORM


def transfer_between_budgets(
    session: Session,
    *,
    source_budget_id: int,
    target_budget_id: int,
    source_category_id: int,
    target_category_id: int,
    amount: float,
    occurred_on: date,
    description: str,
) -> tuple[TransactionRecordORM, TransactionRecordORM]:
    """Atomically move money from one budget to another using two transactions."""

    try:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")

        source_budget = session.get(BudgetRecord, source_budget_id)
        target_budget = session.get(BudgetRecord, target_budget_id)
        source_category = session.get(CategoryRecord, source_category_id)
        target_category = session.get(CategoryRecord, target_category_id)

        if source_budget is None or target_budget is None:
            raise ValueError("Budget was not found.")
        if source_category is None or target_category is None:
            raise ValueError("Category was not found.")
        if source_category.budget_id != source_budget.id:
            raise ValueError("Source category does not belong to source budget.")
        if target_category.budget_id != target_budget.id:
            raise ValueError("Target category does not belong to target budget.")
        if source_budget.currency != target_budget.currency:
            raise ValueError("Cannot transfer between different currencies.")

        expense = TransactionRecordORM(
            budget_id=source_budget.id,
            category_id=source_category.id,
            occurred_on=occurred_on,
            transaction_type="expense",
            amount=amount,
            description=description,
        )
        income = TransactionRecordORM(
            budget_id=target_budget.id,
            category_id=target_category.id,
            occurred_on=occurred_on,
            transaction_type="income",
            amount=amount,
            description=description,
        )
        session.add_all([expense, income])
        session.commit()
        session.refresh(expense)
        session.refresh(income)
        return expense, income
    except Exception:
        session.rollback()
        raise
