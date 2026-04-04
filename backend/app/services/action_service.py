from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.recorder import record_audit_log
from app.models.action import Action
from app.models.email import Email
from app.models.enums import AuditEventType, EmailStatus
from app.schemas.email import EmailActionRequest


class ActionService:
    async def create_action(self, session: AsyncSession, *, email: Email, payload: EmailActionRequest) -> Action:
        action = Action(
            email_id=email.id,
            action_type=payload.action_type,
            reason=payload.reason,
            actor=payload.actor,
            metadata_json=payload.metadata_json,
        )
        session.add(action)
        email.status = EmailStatus.ACTIONED
        await session.flush()
        await record_audit_log(
            session,
            event_type=AuditEventType.EMAIL_ACTIONED,
            actor=payload.actor,
            resource_type="email",
            resource_id=email.id,
            message=f"Action {payload.action_type.value} applied",
            details=payload.model_dump(),
        )
        return action
