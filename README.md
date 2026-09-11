# Finance Tracker

Laboratory project for the Professional Python course.

Variant 12 uses one cross-lab domain: finance tracker.

- Laboratory work 1: project structure and basic finance tracker logic.
- Laboratory work 2: structured finance transaction analysis.
- Laboratory work 3: streaming transaction processing.
- Laboratory work 4: professional typed OOP domain model.
- Laboratory work 5: reliable CSV import, YAML configuration, logging and JSON export.
- Laboratory work 6: pytest test suite, mocks, tmp_path, monkeypatch and coverage.
- Laboratory work 7: SQLite persistence layer, SQLAlchemy ORM, migrations and repositories.
- Laboratory work 8: FastAPI REST API, Pydantic schemas, async tasks and HTTPX.

## Description

Console application for finance tracking laboratory works. The project
demonstrates src-layout packaging, structured data processing, streaming I/O,
typed OOP design, custom exceptions, configuration, logging, validation and
atomic export, automated testing with coverage, and database persistence.

The current entry point demonstrates the laboratory work 7 SQLite persistence
layer. Laboratory work 8 exposes the persistence layer through a FastAPI REST API.

## Requirements

Python 3.11+

## Installation

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

## Run

```bash
python -m finance_tracker.main
```

or:

```bash
finance-tracker
```

## Tests

```bash
python -m unittest discover -s tests
python -m pytest --cov=finance_tracker --cov-branch --cov-report=term-missing
python -m mypy src
```

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

## Author

Student: Roman Mariana
Group: FEP-32
