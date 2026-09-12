"""FastAPI REST API for the finance tracker."""

from __future__ import annotations

from collections.abc import Generator
import asyncio

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from finance_tracker import __version__
from finance_tracker.config import get_settings
from finance_tracker.database import SessionLocal, create_schema, engine
from finance_tracker.db_models import BudgetRecord, CategoryRecord, TransactionRecordORM
from finance_tracker.db_repositories import (
    BudgetRepository,
    CategoryRepository,
    TransactionRepository,
)
from finance_tracker.external_api import fetch_many_json_with_timeout
from finance_tracker.schemas import (
    BatchFetchRequest,
    BudgetCreate,
    BudgetResponse,
    BudgetSummaryResponse,
    BudgetUpdate,
    CategoryCreate,
    CategoryResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)


app = FastAPI(
    title=get_settings().app_name,
    version=__version__,
)


@app.on_event("startup")
async def startup() -> None:
    """Create SQLite schema for local demo runs."""

    if getattr(app.state, "testing", False):
        return
    create_schema(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "environment": get_settings().environment,
    }


@app.get("/budgets", response_model=list[BudgetResponse], tags=["budgets"])
async def list_budgets(
    currency: str | None = Query(default=None, min_length=3, max_length=3),
    session: Session = Depends(get_session),
) -> list[BudgetRecord]:
    budgets = BudgetRepository(session).list_all()
    if currency is not None:
        return [budget for budget in budgets if budget.currency == currency]
    return budgets


@app.post(
    "/budgets",
    response_model=BudgetResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["budgets"],
)
async def create_budget(
    payload: BudgetCreate,
    session: Session = Depends(get_session),
) -> object:
    try:
        return BudgetRepository(session).add(payload.name, payload.currency)
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Budget already exists.",
        ) from error


@app.get("/budgets/{budget_id}", response_model=BudgetResponse, tags=["budgets"])
async def get_budget(
    budget_id: int,
    session: Session = Depends(get_session),
) -> object:
    budget = BudgetRepository(session).get_by_id(budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found.")
    return budget


@app.patch("/budgets/{budget_id}", response_model=BudgetResponse, tags=["budgets"])
async def update_budget(
    budget_id: int,
    payload: BudgetUpdate,
    session: Session = Depends(get_session),
) -> object:
    if payload.name is None:
        return await get_budget(budget_id, session)
    try:
        budget = BudgetRepository(session).update_name(budget_id, payload.name)
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=409, detail="Budget name already exists.") from error
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found.")
    return budget


@app.delete("/budgets/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["budgets"])
async def delete_budget(
    budget_id: int,
    session: Session = Depends(get_session),
) -> Response:
    deleted = BudgetRepository(session).delete(budget_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Budget not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post(
    "/budgets/{budget_id}/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["categories"],
)
async def create_category(
    budget_id: int,
    payload: CategoryCreate,
    session: Session = Depends(get_session),
) -> object:
    _require_budget(session, budget_id)
    try:
        return CategoryRepository(session).add(
            budget_id,
            payload.name,
            payload.spending_limit_amount,
        )
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=409, detail="Category already exists.") from error


@app.get(
    "/budgets/{budget_id}/categories",
    response_model=list[CategoryResponse],
    tags=["categories"],
)
async def list_categories(
    budget_id: int,
    session: Session = Depends(get_session),
) -> list[CategoryRecord]:
    _require_budget(session, budget_id)
    return CategoryRepository(session).list_for_budget(budget_id)


@app.post(
    "/budgets/{budget_id}/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["transactions"],
)
async def create_transaction(
    budget_id: int,
    payload: TransactionCreate,
    session: Session = Depends(get_session),
) -> object:
    _require_budget(session, budget_id)
    category = CategoryRepository(session).get_by_id(payload.category_id)
    if category is None or category.budget_id != budget_id:
        raise HTTPException(status_code=404, detail="Category not found.")
    try:
        return TransactionRepository(session).add(
            budget_id=budget_id,
            category_id=payload.category_id,
            occurred_on=payload.occurred_on,
            transaction_type=payload.transaction_type,
            amount=payload.amount,
            description=payload.description,
            notes=payload.notes,
        )
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(status_code=400, detail="Invalid transaction.") from error


@app.get(
    "/budgets/{budget_id}/transactions",
    response_model=list[TransactionResponse],
    tags=["transactions"],
)
async def list_transactions(
    budget_id: int,
    transaction_type: str | None = Query(default=None, pattern="^(income|expense)$"),
    category_id: int | None = Query(default=None, gt=0),
    session: Session = Depends(get_session),
) -> list[TransactionRecordORM]:
    _require_budget(session, budget_id)
    repository = TransactionRepository(session)
    transactions = repository.list_for_budget(budget_id)
    if transaction_type is not None:
        transactions = [
            transaction
            for transaction in transactions
            if transaction.transaction_type == transaction_type
        ]
    if category_id is not None:
        transactions = [
            transaction for transaction in transactions if transaction.category_id == category_id
        ]
    return transactions


@app.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    tags=["transactions"],
)
async def get_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
) -> object:
    return _require_transaction(session, transaction_id)


@app.patch(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    tags=["transactions"],
)
async def update_transaction(
    transaction_id: int,
    payload: TransactionUpdate,
    session: Session = Depends(get_session),
) -> object:
    transaction = _require_transaction(session, transaction_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(transaction, field, value)
    session.commit()
    session.refresh(transaction)
    return transaction


@app.delete(
    "/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["transactions"],
)
async def delete_transaction(
    transaction_id: int,
    session: Session = Depends(get_session),
) -> Response:
    deleted = TransactionRepository(session).delete(transaction_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get(
    "/budgets/{budget_id}/summary",
    response_model=BudgetSummaryResponse,
    tags=["budgets"],
)
async def get_budget_summary(
    budget_id: int,
    session: Session = Depends(get_session),
) -> BudgetSummaryResponse:
    _require_budget(session, budget_id)
    repository = TransactionRepository(session)
    balance_task = asyncio.create_task(_balance(repository, budget_id))
    income_task = asyncio.create_task(_total(repository, budget_id, "income"))
    expense_task = asyncio.create_task(_total(repository, budget_id, "expense"))
    counts_task = asyncio.create_task(_category_counts(repository, budget_id))
    balance, income, expenses, category_counts = await asyncio.gather(
        balance_task,
        income_task,
        expense_task,
        counts_task,
    )
    return BudgetSummaryResponse(
        budget_id=budget_id,
        balance=balance,
        income=income,
        expenses=expenses,
        category_counts=category_counts,
    )


@app.post("/external/batch", tags=["async"])
async def external_batch_fetch(
    payload: BatchFetchRequest,
) -> list[dict[str, Any]]:
    try:
        return await fetch_many_json_with_timeout(
            [str(url) for url in payload.urls],
            timeout_seconds=payload.timeout_seconds,
            attempts=payload.attempts,
            concurrency_limit=payload.concurrency_limit,
        )
    except TimeoutError as error:
        raise HTTPException(status_code=504, detail="Batch operation timed out.") from error


async def _balance(
    repository: TransactionRepository,
    budget_id: int,
) -> float:
    await asyncio.sleep(0)
    return repository.balance(budget_id)


async def _total(
    repository: TransactionRepository,
    budget_id: int,
    transaction_type: str,
) -> float:
    await asyncio.sleep(0)
    return repository.total_by_type(budget_id, transaction_type)


async def _category_counts(
    repository: TransactionRepository,
    budget_id: int,
) -> list[tuple[str, int]]:
    await asyncio.sleep(0)
    return repository.count_by_category(budget_id)


def _require_budget(
    session: Session,
    budget_id: int,
) -> object:
    budget = BudgetRepository(session).get_by_id(budget_id)
    if budget is None:
        raise HTTPException(status_code=404, detail="Budget not found.")
    return budget


def _require_transaction(
    session: Session,
    transaction_id: int,
) -> TransactionRecordORM:
    transaction = TransactionRepository(session).get_by_id(transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return transaction
