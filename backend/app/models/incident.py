from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import IncidentStatus, RiskLevel, sql_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Incident(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_email_id", "email_id"),
        Index("ix_incidents_status", "status"),
    )

    email_id: Mapped[str] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), nullable=False)
    analysis_result_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_results.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[IncidentStatus] = mapped_column(
        sql_enum(IncidentStatus),
        default=IncidentStatus.OPEN,
        nullable=False,
    )
    risk_level: Mapped[RiskLevel] = mapped_column(sql_enum(RiskLevel), nullable=False)

    email: Mapped["Email"] = relationship(back_populates="incidents")
