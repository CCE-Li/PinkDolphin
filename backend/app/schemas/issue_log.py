from typing import Any

from app.models.enums import IssueSeverity
from app.schemas.common import TimestampedSchema


class IssueLogRead(TimestampedSchema):
    component: str
    severity: IssueSeverity
    message: str
    details: dict[str, Any]
