"""baseline schema

Revision ID: 20260404_0010
Revises:
Create Date: 2026-04-04 00:10:00.000000
"""

from collections.abc import Sequence

from alembic import op

from app.db.base import Base
from app.models import *  # noqa: F401,F403

# revision identifiers, used by Alembic.
revision: str = "20260404_0010"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
