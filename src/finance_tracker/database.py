"""SQLite database setup for the finance tracker persistence layer."""

from __future__ import annotations

from pathlib import Path
import sqlite3

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from finance_tracker.db_models import Base


DATABASE_PATH = Path("data") / "finance_tracker.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


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

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(target_engine)


def drop_schema(
    target_engine: Engine = engine,
) -> None:
    """Drop all finance tracker tables."""

    Base.metadata.drop_all(target_engine)


def session_scope() -> Session:
    """Create a Session for simple application scripts."""

    return SessionLocal()
