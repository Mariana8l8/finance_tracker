# Finance Tracker

Production-oriented laboratory project for the Professional Python course.

Variant 12 uses one cross-lab domain: finance tracker.

- Laboratory work 1: project structure and basic finance tracker logic.
- Laboratory work 2: structured finance transaction analysis.
- Laboratory work 3: streaming transaction processing.
- Laboratory work 4: professional typed OOP domain model.
- Laboratory work 5: reliable CSV import, YAML configuration, logging and JSON export.
- Laboratory work 6: pytest test suite, mocks, tmp_path, monkeypatch and coverage.
- Laboratory work 7: SQLite persistence layer, SQLAlchemy ORM, migrations and repositories.
- Laboratory work 8: FastAPI REST API, Pydantic schemas, async tasks and HTTPX.
- Laboratory work 9: performance profiling, concurrency, multiprocessing, NumPy and caching.
- Laboratory work 10: packaging, environment configuration, Docker, CI/CD and release readiness.

## Description

Finance Tracker is a typed Python project that evolved from a console finance
tracker into a FastAPI REST API with SQLite persistence, file import/export,
automated tests, profiling benchmarks, Docker support and GitHub Actions CI.

The API exposes budgets, categories, transactions and summary statistics. The
project keeps configuration in environment variables and does not store secrets
in source code.

## Features

- src-layout installable Python package.
- FastAPI REST API with OpenAPI docs at `/docs`.
- SQLite persistence through SQLAlchemy repositories.
- CSV import and JSON export pipeline.
- Async HTTPX helpers.
- Performance benchmarks with Python loops, threads, processes, NumPy and caching.
- Pytest, mypy, Ruff, package build and Docker build in CI.

## Requirements

Python 3.11+

For Docker runs, Docker Engine is required.

## Installation

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

## Configuration

Copy the example environment file for local changes:

```bash
cp .env.example .env
```

Supported environment variables:

```text
FINANCE_TRACKER_APP_NAME=Finance Tracker API
APP_ENV=development
DATABASE_URL=sqlite:///data/finance_tracker.db
LOG_LEVEL=INFO
```

Do not commit `.env` or real secrets. The tracked `.env.example` contains only
safe placeholder values.

## Run Console Demo

```bash
python -m finance_tracker.main
```

or:

```bash
finance-tracker
```

## Run API

```bash
uvicorn finance_tracker.api:app --reload
```

Useful endpoints:

```text
GET /health
GET /budgets
POST /budgets
GET /budgets/{budget_id}/transactions
GET /budgets/{budget_id}/summary
```

API docs:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
http://127.0.0.1:8000/openapi.json
```

## Tests

```bash
ruff check .
ruff format --check .
python -m mypy src
python -m pytest --cov=finance_tracker --cov-branch --cov-report=term-missing
```

## Package Build

```bash
python -m build
```

Expected artifacts:

```text
dist/finance_tracker-1.0.0-py3-none-any.whl
dist/finance_tracker-1.0.0.tar.gz
```

## Docker

Build image:

```bash
docker build -t finance-tracker:1.0 .
```

Run container:

```bash
docker run --rm -p 8000:8000 finance-tracker:1.0
```

Run with production environment and persistent SQLite volume:

```bash
docker run --rm -p 8000:8000 \
  -e APP_ENV=production \
  -e LOG_LEVEL=INFO \
  -e DATABASE_URL=sqlite:////app/data/finance_tracker.db \
  -v finance_tracker_data:/app/data \
  finance-tracker:1.0
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## CI/CD

GitHub Actions workflow: `.github/workflows/ci.yml`.

The pipeline runs:

```text
ruff check
ruff format --check
mypy src
pytest -v
python -m build
docker build
```

## Production Checklist

- Tests pass.
- Lint and format checks pass.
- Type checking passes.
- Wheel and sdist build successfully.
- `.env` is ignored and `.env.example` is tracked.
- No secrets are stored in source code, README or Dockerfile.
- Docker image builds and runs as a non-root user.
- `/health` returns `200`.
- GitHub Actions workflow is present.

## Laboratory 5 Files

```text
config/lab5_config.yaml
examples/lab5_transactions.csv
src/finance_tracker/exceptions.py
src/finance_tracker/config.py
src/finance_tracker/logging_config.py
src/finance_tracker/file_utils.py
src/finance_tracker/file_pipeline.py
src/finance_tracker/file_exporters.py
tests/test_file_pipeline.py
tests/conftest.py
tests/unit/
tests/integration/
```

## Laboratory 7 Files

```text
alembic.ini
migrations/
src/finance_tracker/database.py
src/finance_tracker/db_models.py
src/finance_tracker/db_repositories.py
src/finance_tracker/db_services.py
src/finance_tracker/dbapi.py
tests/integration/test_database_persistence_pytest.py
```

## Laboratory 8 Files

```text
src/finance_tracker/api.py
src/finance_tracker/schemas.py
src/finance_tracker/external_api.py
tests/integration/test_api_pytest.py
```

Run the API:

```bash
uvicorn finance_tracker.api:app --reload
```

## Laboratory 9 Files

```text
src/finance_tracker/performance.py
src/finance_tracker/profiling.py
benchmarks/benchmark_lab09.py
tests/test_performance_lab09.py
```

Run the performance benchmark:

```bash
python benchmarks/benchmark_lab09.py
```

## Laboratory 10 Files

```text
.env.example
.dockerignore
Dockerfile
.github/workflows/ci.yml
LICENSE
```

## Author

Student: Roman Mariana
Group: FEP-32
