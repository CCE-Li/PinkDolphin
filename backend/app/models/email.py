from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import EmailSource, EmailStatus
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Email(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "emails"
    __table_args__ = (
        Index("ix_emails_message_id", "message_id"),
        Index("ix_emails_subject", "subject"),
        Index("ix_emails_status", "status"),
        Index("ix_emails_mailbox_account_id", "mailbox_account_id"),
        UniqueConstraint("mailbox_account_id", "remote_folder", "remote_uid", name="uq_emails_mailbox_account_folder_remote_uid"),
    )

    message_id: Mapped[str | None] = mapped_column(String(512), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    authentication_results: Mapped[str | None] = mapped_column(Text, nullable=True)
    send_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_headers: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[EmailSource] = mapped_column(Enum(EmailSource, native_enum=False), nullable=False)
    raw_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    mailbox_account_id: Mapped[str | None] = mapped_column(ForeignKey("mail_accounts.id", ondelete="SET NULL"), nullable=True)
    remote_uid: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    remote_folder: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[EmailStatus] = mapped_column(
        Enum(EmailStatus, native_enum=False),
        default=EmailStatus.RECEIVED,
        nullable=False,
    )
    latest_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_results.id"), nullable=True)
    latest_risk_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    latest_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    addresses: Mapped[list["EmailAddress"]] = relationship(back_populates="email", cascade="all, delete-orphan")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="email", cascade="all, delete-orphan")
    urls: Mapped[list["Url"]] = relationship(back_populates="email", cascade="all, delete-orphan")
    analysis_results: Mapped[list["AnalysisResult"]] = relationship(
        back_populates="email",
        foreign_keys="AnalysisResult.email_id",
        cascade="all, delete-orphan",
    )
    user_reports: Mapped[list["UserReport"]] = relationship(back_populates="email")
    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="email",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    actions: Mapped[list["Action"]] = relationship(
        back_populates="email",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    mail_account: Mapped["MailAccount | None"] = relationship(back_populates="emails")
