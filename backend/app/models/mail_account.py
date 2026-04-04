from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MailboxProvider, MailboxStatus, sql_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MailAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mail_accounts"
    __table_args__ = (
        Index("ix_mail_accounts_owner_email", "owner_email"),
        Index("ix_mail_accounts_email_address", "email_address", unique=True),
        Index("ix_mail_accounts_is_active", "is_active"),
    )

    owner_email: Mapped[str] = mapped_column(String(320), nullable=False)
    email_address: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider: Mapped[MailboxProvider] = mapped_column(sql_enum(MailboxProvider), nullable=False)
    imap_host: Mapped[str] = mapped_column(String(255), nullable=False)
    imap_port: Mapped[int] = mapped_column(Integer, nullable=False, default=993)
    imap_username: Mapped[str] = mapped_column(String(320), nullable=False)
    imap_password: Mapped[str] = mapped_column(Text, nullable=False)
    mailbox_folder: Mapped[str] = mapped_column(String(255), nullable=False, default="INBOX")
    use_ssl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[MailboxStatus] = mapped_column(
        sql_enum(MailboxStatus),
        nullable=False,
        default=MailboxStatus.IDLE,
    )
    listen_interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    connect_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    last_seen_uid: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_synced_uid: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    emails: Mapped[list["Email"]] = relationship(back_populates="mail_account")
