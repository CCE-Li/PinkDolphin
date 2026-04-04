"""expand enum varchar lengths

Revision ID: 20260404_0011
Revises: 20260404_0010
Create Date: 2026-04-04 23:40:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260404_0011"
down_revision: str | Sequence[str] | None = "20260404_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("mail_accounts", "provider", type_=sa.String(length=11), existing_nullable=False)
    op.alter_column("mail_accounts", "status", type_=sa.String(length=9), existing_nullable=False)
    op.alter_column("actions", "action_type", type_=sa.String(length=14), existing_nullable=False)
    op.alter_column("analysis_results", "risk_level", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("analysis_results", "recommended_action", type_=sa.String(length=14), existing_nullable=False)
    op.alter_column("analyzer_results", "status", type_=sa.String(length=7), existing_nullable=False)
    op.alter_column("analyzer_results", "severity", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("audit_logs", "event_type", type_=sa.String(length=19), existing_nullable=False)
    op.alter_column("emails", "source", type_=sa.String(length=11), existing_nullable=False)
    op.alter_column("emails", "status", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("email_addresses", "role", type_=sa.String(length=11), existing_nullable=False)
    op.alter_column("incidents", "status", type_=sa.String(length=13), existing_nullable=False)
    op.alter_column("incidents", "risk_level", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("issue_logs", "severity", type_=sa.String(length=7), existing_nullable=False)
    op.alter_column("allowlists", "list_type", type_=sa.String(length=7), existing_nullable=False)
    op.alter_column("denylists", "list_type", type_=sa.String(length=7), existing_nullable=False)
    op.alter_column("rules", "condition_type", type_=sa.String(length=16), existing_nullable=False)
    op.alter_column("rules", "severity", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("rules", "override_action", type_=sa.String(length=14), existing_nullable=True)


def downgrade() -> None:
    op.alter_column("rules", "override_action", type_=sa.String(length=10), existing_nullable=True)
    op.alter_column("rules", "severity", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("rules", "condition_type", type_=sa.String(length=15), existing_nullable=False)
    op.alter_column("denylists", "list_type", type_=sa.String(length=7), existing_nullable=False)
    op.alter_column("allowlists", "list_type", type_=sa.String(length=7), existing_nullable=False)
    op.alter_column("issue_logs", "severity", type_=sa.String(length=7), existing_nullable=False)
    op.alter_column("incidents", "risk_level", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("incidents", "status", type_=sa.String(length=13), existing_nullable=False)
    op.alter_column("email_addresses", "role", type_=sa.String(length=10), existing_nullable=False)
    op.alter_column("emails", "status", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("emails", "source", type_=sa.String(length=11), existing_nullable=False)
    op.alter_column("audit_logs", "event_type", type_=sa.String(length=19), existing_nullable=False)
    op.alter_column("analyzer_results", "severity", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("analyzer_results", "status", type_=sa.String(length=7), existing_nullable=False)
    op.alter_column("analysis_results", "recommended_action", type_=sa.String(length=14), existing_nullable=False)
    op.alter_column("analysis_results", "risk_level", type_=sa.String(length=8), existing_nullable=False)
    op.alter_column("actions", "action_type", type_=sa.String(length=14), existing_nullable=False)
    op.alter_column("mail_accounts", "status", type_=sa.String(length=9), existing_nullable=False)
    op.alter_column("mail_accounts", "provider", type_=sa.String(length=7), existing_nullable=False)
