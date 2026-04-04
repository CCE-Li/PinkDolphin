from sqlalchemy import ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AnalyzerExecutionStatus, RecommendedAction, RiskLevel, SeverityLevel, sql_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class AnalysisResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analysis_results"
    __table_args__ = (
        Index("ix_analysis_results_email_id", "email_id"),
        Index("ix_analysis_results_risk_level", "risk_level"),
    )

    email_id: Mapped[str] = mapped_column(ForeignKey("emails.id", ondelete="CASCADE"), nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(sql_enum(RiskLevel), nullable=False)
    recommended_action: Mapped[RecommendedAction] = mapped_column(
        sql_enum(RecommendedAction),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    override_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    email: Mapped["Email"] = relationship(back_populates="analysis_results", foreign_keys=[email_id])
    analyzer_results: Mapped[list["AnalyzerResult"]] = relationship(
        back_populates="analysis_result",
        cascade="all, delete-orphan",
    )


class AnalyzerResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "analyzer_results"
    __table_args__ = (
        Index("ix_analyzer_results_analysis_result_id", "analysis_result_id"),
        Index("ix_analyzer_results_analyzer_name", "analyzer_name"),
    )

    analysis_result_id: Mapped[str] = mapped_column(
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False,
    )
    analyzer_name: Mapped[str] = mapped_column(String(128), nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    status: Mapped[AnalyzerExecutionStatus] = mapped_column(
        sql_enum(AnalyzerExecutionStatus),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    severity: Mapped[SeverityLevel] = mapped_column(sql_enum(SeverityLevel), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    signals: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    analysis_result: Mapped["AnalysisResult"] = relationship(back_populates="analyzer_results")
