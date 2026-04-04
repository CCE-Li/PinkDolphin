from sqlalchemy import Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PrivacySetting(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "privacy_settings"

    skip_url_on_sender_allowlist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_attachment_on_sender_allowlist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_llm_on_sender_allowlist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
