from typing import Any

from app.models.enums import AuditEventType
from app.schemas.common import TimestampedSchema


class AuditLogRead(TimestampedSchema):
    event_type: AuditEventType
    actor: str
    resource_type: str
    resource_id: str
    details: dict[str, Any]
    message: str

