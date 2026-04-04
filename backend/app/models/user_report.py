from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class UserReport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_reports"
    __table_args__ = (Index("ix_user_reports_email_id", "email_id"),)

    email_id: Mapped[str | None] = mapped_column(ForeignKey("emails.id"), nullable=True)
    reporter_email: Mapped[str] = mapped_column(String(320), nullable=False)
    reporter_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    raw_email: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    email: Mapped["Email | None"] = relationship(back_populates="user_reports")

