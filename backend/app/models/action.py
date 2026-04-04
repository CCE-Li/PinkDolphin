from sqlalchemy import ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ActionType, sql_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Action(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "actions"
    __table_args__ = (Index("ix_actions_email_id", "email_id"),)

    email_id: Mapped[str] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[ActionType] = mapped_column(sql_enum(ActionType), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str] = mapped_column(String(128), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    email: Mapped["Email"] = relationship(back_populates="actions")
