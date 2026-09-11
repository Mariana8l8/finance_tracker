from __future__ import annotations

from collections.abc import Iterator
import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from finance_tracker.api import app, get_session
from finance_tracker.db_models import Base
from finance_tracker.external_api import fetch_many_json_with_timeout


@pytest.fixture
def api_session(sqlite_engine: Engine) -> Iterator[Session]:
    Base.metadata.create_all(sqlite_engine)
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


@pytest.fixture
def api_client(api_session: Session) -> Iterator[TestClient]:
    def override_session() -> Iterator[Session]:
        yield api_session

    app.dependency_overrides[get_session] = override_session
    app.state.testing = True
    client = TestClient(app)
    try:
        yield client
    finally:
        client.close()
        app.state.testing = False
        app.dependency_overrides.clear()


def test_health_endpoint(api_client: TestClient) -> None:
    response = api_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_budget_category_transaction_crud(api_client: TestClient) -> None:
    budget_response = api_client.post(
        "/budgets",
        json={"name": "September", "currency": "UAH"},
    )
    assert budget_response.status_code == 201
    budget = budget_response.json()

    category_response = api_client.post(
        f"/budgets/{budget['id']}/categories",
        json={"name": "Food", "spending_limit_amount": 2000.0},
    )
    assert category_response.status_code == 201
    category = category_response.json()

    transaction_response = api_client.post(
        f"/budgets/{budget['id']}/transactions",
        json={
            "category_id": category["id"],
            "occurred_on": "2026-09-12",
            "transaction_type": "expense",
            "amount": 150.5,
            "description": "Groceries",
        },
    )
    assert transaction_response.status_code == 201
    transaction = transaction_response.json()

    filtered = api_client.get(
        f"/budgets/{budget['id']}/transactions",
        params={"transaction_type": "expense", "category_id": category["id"]},
    )
    patched = api_client.patch(
        f"/transactions/{transaction['id']}",
        json={"amount": 175.0, "notes": "Updated via API"},
    )
    deleted = api_client.delete(f"/transactions/{transaction['id']}")

    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert patched.status_code == 200
    assert patched.json()["amount"] == 175.0
    assert deleted.status_code == 204
    assert api_client.get(f"/transactions/{transaction['id']}").status_code == 404


def test_budget_validation_and_conflict(api_client: TestClient) -> None:
    invalid = api_client.post("/budgets", json={"name": "A", "currency": "UAH"})
    first = api_client.post("/budgets", json={"name": "Duplicate", "currency": "UAH"})
    second = api_client.post("/budgets", json={"name": "Duplicate", "currency": "UAH"})

    assert invalid.status_code == 422
    assert first.status_code == 201
    assert second.status_code == 409


def test_budget_summary_uses_async_gather(api_client: TestClient) -> None:
    budget = api_client.post(
        "/budgets",
        json={"name": "Summary", "currency": "UAH"},
    ).json()
    salary = api_client.post(
        f"/budgets/{budget['id']}/categories",
        json={"name": "Salary"},
    ).json()
    food = api_client.post(
        f"/budgets/{budget['id']}/categories",
        json={"name": "Food"},
    ).json()
    api_client.post(
        f"/budgets/{budget['id']}/transactions",
        json={
            "category_id": salary["id"],
            "occurred_on": "2026-09-01",
            "transaction_type": "income",
            "amount": 1000.0,
            "description": "Salary",
        },
    )
    api_client.post(
        f"/budgets/{budget['id']}/transactions",
        json={
            "category_id": food["id"],
            "occurred_on": "2026-09-02",
            "transaction_type": "expense",
            "amount": 150.0,
            "description": "Groceries",
        },
    )

    response = api_client.get(f"/budgets/{budget['id']}/summary")

    assert response.status_code == 200
    assert response.json()["balance"] == 850.0
    assert response.json()["category_counts"] == [["Food", 1], ["Salary", 1]]


def test_missing_resources_return_404(api_client: TestClient) -> None:
    assert api_client.get("/budgets/999").status_code == 404
    assert api_client.delete("/transactions/999").status_code == 404


def test_external_httpx_helper_with_asgi_transport(api_session: Session) -> None:
    async def run() -> None:
        def override_session() -> Iterator[Session]:
            yield api_session

        app.dependency_overrides[get_session] = override_session
        app.state.testing = True
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.get("/health")
        app.state.testing = False
        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    asyncio.run(run())


def test_external_batch_helper_uses_httpx_tasks_and_gather(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                status_code=200,
                json={"url": str(request.url)},
            )

        class TransportedAsyncClient(httpx.AsyncClient):
            def __init__(self, *args: object, **kwargs: object) -> None:
                kwargs["transport"] = httpx.MockTransport(handler)
                super().__init__(*args, **kwargs)

        monkeypatch.setattr(httpx, "AsyncClient", TransportedAsyncClient)

        results = await fetch_many_json_with_timeout(
            ["https://example.test/one", "https://example.test/two"],
            timeout_seconds=2.0,
            attempts=2,
            concurrency_limit=1,
        )

        assert results == [
            {"url": "https://example.test/one"},
            {"url": "https://example.test/two"},
        ]

    asyncio.run(run())
