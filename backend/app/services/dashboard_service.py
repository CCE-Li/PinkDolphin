from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import Email
from app.models.enums import EmailStatus, IncidentStatus, MailboxStatus
from app.models.incident import Incident
from app.models.mail_account import MailAccount
from app.schemas.dashboard import DashboardSummary


class DashboardService:
    async def get_summary(self, session: AsyncSession) -> DashboardSummary:
        total_emails = await session.scalar(select(func.count()).select_from(Email)) or 0
        analyzed_emails = await session.scalar(
            select(func.count()).select_from(Email).where(Email.status.in_([EmailStatus.ANALYZED, EmailStatus.ACTIONED]))
        ) or 0
        open_incidents = await session.scalar(
            select(func.count()).select_from(Incident).where(Incident.status != IncidentStatus.RESOLVED)
        ) or 0
        critical_emails = await session.scalar(
            select(func.count()).select_from(Email).where(Email.latest_risk_level == "critical")
        ) or 0
        high_risk_emails = await session.scalar(
            select(func.count()).select_from(Email).where(Email.latest_risk_level.in_(["high", "critical"]))
        ) or 0
        monitored_mailboxes = await session.scalar(select(func.count()).select_from(MailAccount)) or 0
        listening_mailboxes = await session.scalar(
            select(func.count()).select_from(MailAccount).where(MailAccount.status == MailboxStatus.LISTENING)
        ) or 0
        mailbox_errors = await session.scalar(
            select(func.count()).select_from(MailAccount).where(MailAccount.status == MailboxStatus.ERROR)
        ) or 0
        return DashboardSummary(
            total_emails=int(total_emails),
            analyzed_emails=int(analyzed_emails),
            open_incidents=int(open_incidents),
            critical_emails=int(critical_emails),
            high_risk_emails=int(high_risk_emails),
            monitored_mailboxes=int(monitored_mailboxes),
            listening_mailboxes=int(listening_mailboxes),
            mailbox_errors=int(mailbox_errors),
        )
