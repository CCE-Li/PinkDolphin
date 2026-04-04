from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import require_admin_token
from app.schemas.audit import AuditLogRead
from app.services.audit_service import AuditService

router = APIRouter(dependencies=[Depends(require_admin_token)])
audit_service = AuditService()


@router.get("", response_model=list[AuditLogRead])
async def list_audit_logs(session: AsyncSession = Depends(get_db_session)) -> list[AuditLogRead]:
    logs = await audit_service.list_logs(session)
    return [AuditLogRead.model_validate(log) for log in logs]
