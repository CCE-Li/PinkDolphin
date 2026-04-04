from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ContactHistory(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "contact_history"
    __table_args__ = (
        Index("ix_contact_history_sender_recipient", "sender_email", "recipient_email", unique=True),
    )

    sender_email: Mapped[str] = mapped_column(String(320), nullable=False)
    recipient_email: Mapped[str] = mapped_column(String(320), nullable=False)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    seen_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_email_id: Mapped[str | None] = mapped_column(ForeignKey("emails.id"), nullable=True)
