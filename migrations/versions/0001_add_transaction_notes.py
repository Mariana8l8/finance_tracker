"""add transaction notes

Revision ID: 0001_add_transaction_notes
Revises: None
Create Date: 2026-09-12
"""

from __future__ import annotations

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0001_add_transaction_notes"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("notes", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transactions", "notes")
