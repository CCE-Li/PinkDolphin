from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.recorder import record_audit_log
from app.models.analysis import AnalysisResult
from app.models.email import Email
from app.models.enums import AuditEventType, IncidentStatus, RiskLevel
from app.models.incident import Incident


class IncidentService:
    async def list_incidents(self, session: AsyncSession) -> list[Incident]:
        result = await session.execute(select(Incident).order_by(Incident.created_at.desc()))
        return list(result.scalars().all())

    async def ensure_incident_for_risky_email(
        self,
        session: AsyncSession,
        *,
        email: Email,
        analysis_result: AnalysisResult,
    ) -> Incident | None:
        if analysis_result.risk_level not in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
            return None

        stmt = select(Incident).where(
            Incident.email_id == email.id,
            Incident.status.in_([IncidentStatus.OPEN, IncidentStatus.INVESTIGATING]),
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        incident = Incident(
            email_id=email.id,
            analysis_result_id=analysis_result.id,
            title=f"Suspicious email: {email.subject or email.message_id or email.id}",
            description="Created automatically for risky email analysis result",
            risk_level=analysis_result.risk_level,
            status=IncidentStatus.OPEN,
        )
        session.add(incident)
        await session.flush()
        await record_audit_log(
            session,
            event_type=AuditEventType.INCIDENT_CREATED,
            actor="system",
            resource_type="incident",
            resource_id=incident.id,
            message="Incident created for risky email",
            details={"email_id": email.id, "analysis_result_id": analysis_result.id},
        )
        return incident
