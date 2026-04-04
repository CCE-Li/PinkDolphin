from sqlalchemy import Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Url(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "urls"
    __table_args__ = (
        Index("ix_urls_email_id", "email_id"),
        Index("ix_urls_url", "url"),
        Index("ix_urls_domain", "domain"),
    )

    email_id: Mapped[str] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_shortened: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    email: Mapped["Email"] = relationship(back_populates="urls")

