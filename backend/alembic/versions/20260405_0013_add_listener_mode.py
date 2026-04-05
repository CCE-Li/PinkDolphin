"""add listener mode

Revision ID: 20260405_0013
Revises: 20260405_0012
Create Date: 2026-04-05 13:20:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260405_0013"
down_revision: str | Sequence[str] | None = "20260405_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("mail_accounts", sa.Column("listener_mode", sa.String(length=32), nullable=False, server_default="polling"))
    op.alter_column("mail_accounts", "listener_mode", server_default=None)


def downgrade() -> None:
    op.drop_column("mail_accounts", "listener_mode")
