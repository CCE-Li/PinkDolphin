from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MailboxSyncCursor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mailbox_sync_cursors"
    __table_args__ = (
        UniqueConstraint("mail_account_id", "mailbox_folder", name="uq_mailbox_sync_cursors_account_folder"),
        Index("ix_mailbox_sync_cursors_mail_account_id", "mail_account_id"),
    )

    mail_account_id: Mapped[str] = mapped_column(ForeignKey("mail_accounts.id", ondelete="CASCADE"), nullable=False)
    mailbox_folder: Mapped[str] = mapped_column(String(255), nullable=False)
    last_seen_uid: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_synced_uid: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
