from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    async def list_logs(self, session: AsyncSession) -> list[AuditLog]:
        result = await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()))
        return list(result.scalars().all())
