from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.recorder import record_audit_log
from app.models.enums import AuditEventType
from app.models.user_report import UserReport
from app.schemas.report import UserReportCreate


class ReportService:
    async def list_reports(self, session: AsyncSession) -> list[UserReport]:
        result = await session.execute(select(UserReport).order_by(UserReport.created_at.desc()))
        return list(result.scalars().all())

    async def create_report(self, session: AsyncSession, payload: UserReportCreate) -> UserReport:
        report = UserReport(**payload.model_dump())
        session.add(report)
        await session.flush()
        await record_audit_log(
            session,
            event_type=AuditEventType.USER_REPORT_CREATED,
            actor=payload.reporter_email,
            resource_type="user_report",
            resource_id=report.id,
            message="User report created",
            details=payload.model_dump(),
        )
        return report
