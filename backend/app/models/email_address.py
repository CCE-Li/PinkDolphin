from sqlalchemy import Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AddressRole
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class EmailAddress(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "email_addresses"
    __table_args__ = (
        Index("ix_email_addresses_email_id", "email_id"),
        Index("ix_email_addresses_address", "address"),
    )

    email_id: Mapped[str] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(String(320), nullable=False)
    role: Mapped[AddressRole] = mapped_column(Enum(AddressRole, native_enum=False), nullable=False)

    email: Mapped["Email"] = relationship(back_populates="addresses")

