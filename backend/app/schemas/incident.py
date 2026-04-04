from app.models.enums import IncidentStatus, RiskLevel
from app.schemas.common import TimestampedSchema


class IncidentRead(TimestampedSchema):
    email_id: str
    analysis_result_id: str | None
    title: str
    description: str | None
    status: IncidentStatus
    risk_level: RiskLevel

