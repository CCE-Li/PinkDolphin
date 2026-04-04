from sqlalchemy import Index, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import IssueSeverity, sql_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class IssueLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "issue_logs"
    __table_args__ = (
        Index("ix_issue_logs_created_at", "created_at"),
        Index("ix_issue_logs_component", "component"),
        Index("ix_issue_logs_severity", "severity"),
    )

    component: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[IssueSeverity] = mapped_column(sql_enum(IssueSeverity), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
