from sqlalchemy import Boolean, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import ListType
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Allowlist(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "allowlists"
    __table_args__ = (Index("ix_allowlists_value", "value"),)

    list_type: Mapped[ListType] = mapped_column(Enum(ListType, native_enum=False), nullable=False)
    value: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    skip_url_scan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_attachment_scan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_llm_scan: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class Denylist(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "denylists"
    __table_args__ = (Index("ix_denylists_value", "value"),)

    list_type: Mapped[ListType] = mapped_column(Enum(ListType, native_enum=False), nullable=False)
    value: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
