from typing import Any

from pydantic import BaseModel

from app.models.enums import AnalyzerExecutionStatus, RecommendedAction, RiskLevel, SeverityLevel
from app.schemas.common import TimestampedSchema


class AnalyzerOutput(BaseModel):
    analyzer_name: str
    enabled: bool = True
    status: AnalyzerExecutionStatus = AnalyzerExecutionStatus.SUCCESS
    score: int
    severity: SeverityLevel
    summary: str
    signals: list[str]
    evidence: dict[str, Any]


class AnalyzerResultRead(TimestampedSchema):
    analysis_result_id: str
    analyzer_name: str
    enabled: bool
    status: AnalyzerExecutionStatus
    score: int
    severity: SeverityLevel
    summary: str
    signals: list[str]
    evidence: dict[str, Any]


class AnalysisResultRead(TimestampedSchema):
    email_id: str
    total_score: int
    risk_level: RiskLevel
    recommended_action: RecommendedAction
    summary: str
    override_reason: str | None
    decision_details: dict[str, Any]
    analyzer_results: list[AnalyzerResultRead] = []
