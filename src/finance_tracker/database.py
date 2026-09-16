"""SQLite database setup for the finance tracker persistence layer."""

from __future__ import annotations

from pathlib import Path
import sqlite3

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from finance_tracker.config import get_settings
from finance_tracker.db_models import Base


DATABASE_PATH = Path("data") / "finance_tracker.db"
DATABASE_URL = get_settings().database_url


def create_sqlite_engine(
    database_url: str = DATABASE_URL,
) -> Engine:
    """Create a SQLite engine with foreign key enforcement enabled."""

    engine = create_engine(
        database_url,
        future=True,
        poolclass=NullPool,
    )

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(
        dbapi_connection: object,
        connection_record: object,
    ) -> None:
        del connection_record
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_sqlite_engine()
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    future=True,
)


def create_schema(
    target_engine: Engine = engine,
) -> None:
    """Create all finance tracker tables."""

    _ensure_sqlite_parent(target_engine)
    Base.metadata.create_all(target_engine)


def drop_schema(
    target_engine: Engine = engine,
) -> None:
    """Drop all finance tracker tables."""

    Base.metadata.drop_all(target_engine)


def session_scope() -> Session:
    """Create a Session for simple application scripts."""

    return SessionLocal()


def _ensure_sqlite_parent(
    target_engine: Engine,
) -> None:
    database_url = str(target_engine.url)
    if not database_url.startswith("sqlite:///"):
        return

    path_value = database_url.removeprefix("sqlite:///")
    if path_value == ":memory:":
        return

    Path(path_value).parent.mkdir(parents=True, exist_ok=True)
