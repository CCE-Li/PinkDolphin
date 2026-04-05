"""add graph outlook support

Revision ID: 20260405_0012
Revises: 20260404_0011
Create Date: 2026-04-05 12:30:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260405_0012"
down_revision: str | Sequence[str] | None = "20260404_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("mail_accounts", sa.Column("auth_type", sa.String(length=32), nullable=False, server_default="password"))
    op.add_column("mail_accounts", sa.Column("sync_mode", sa.String(length=32), nullable=False, server_default="imap"))
    op.add_column("mail_accounts", sa.Column("oauth_access_token", sa.Text(), nullable=True))
    op.add_column("mail_accounts", sa.Column("oauth_refresh_token", sa.Text(), nullable=True))
    op.add_column("mail_accounts", sa.Column("oauth_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("mail_accounts", sa.Column("oauth_scope", sa.Text(), nullable=True))
    op.add_column("mail_accounts", sa.Column("oauth_subject", sa.String(length=255), nullable=True))
    op.add_column("mail_accounts", sa.Column("graph_delta_link", sa.Text(), nullable=True))
    op.add_column("emails", sa.Column("remote_message_id", sa.String(length=512), nullable=True))
    op.create_index("ix_emails_remote_message_id", "emails", ["remote_message_id"], unique=False)

    op.execute("UPDATE mail_accounts SET auth_type = 'oauth2', sync_mode = 'graph', imap_host = 'graph.microsoft.com', imap_port = 443 WHERE provider = 'OUTLOOK'")

    op.alter_column("mail_accounts", "auth_type", server_default=None)
    op.alter_column("mail_accounts", "sync_mode", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_emails_remote_message_id", table_name="emails")
    op.drop_column("emails", "remote_message_id")
    op.drop_column("mail_accounts", "graph_delta_link")
    op.drop_column("mail_accounts", "oauth_subject")
    op.drop_column("mail_accounts", "oauth_scope")
    op.drop_column("mail_accounts", "oauth_token_expires_at")
    op.drop_column("mail_accounts", "oauth_refresh_token")
    op.drop_column("mail_accounts", "oauth_access_token")
    op.drop_column("mail_accounts", "sync_mode")
    op.drop_column("mail_accounts", "auth_type")
