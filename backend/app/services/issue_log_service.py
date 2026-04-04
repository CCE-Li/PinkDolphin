from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import db_manager
from app.models.enums import IssueSeverity
from app.models.issue_log import IssueLog


class IssueLogService:
    async def list_logs(self, session: AsyncSession) -> list[IssueLog]:
        result = await session.execute(select(IssueLog).order_by(IssueLog.created_at.desc()))
        return list(result.scalars().all())

    async def log(
        self,
        session: AsyncSession,
        *,
        component: str,
        severity: IssueSeverity,
        message: str,
        details: dict,
    ) -> IssueLog:
        entry = IssueLog(component=component, severity=severity, message=message, details=details)
        session.add(entry)
        await session.flush()
        return entry

    async def log_detached(
        self,
        *,
        component: str,
        severity: IssueSeverity,
        message: str,
        details: dict,
    ) -> IssueLog | None:
        try:
            async with db_manager.session() as session:
                entry = IssueLog(component=component, severity=severity, message=message, details=details)
                session.add(entry)
                await session.flush()
                return entry
        except Exception:
            return None
