from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.enums import AuditEventType


async def record_audit_log(
    session: AsyncSession,
    *,
    event_type: AuditEventType,
    actor: str,
    resource_type: str,
    resource_id: str,
    message: str,
    details: dict,
) -> AuditLog:
    entry = AuditLog(
        event_type=event_type,
        actor=actor,
        resource_type=resource_type,
        resource_id=resource_id,
        message=message,
        details=details,
    )
    session.add(entry)
    await session.flush()
    return entry
