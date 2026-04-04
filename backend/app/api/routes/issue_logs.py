from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import require_admin_token
from app.schemas.issue_log import IssueLogRead
from app.services.issue_log_service import IssueLogService

router = APIRouter(dependencies=[Depends(require_admin_token)])
issue_log_service = IssueLogService()


@router.get("", response_model=list[IssueLogRead])
async def list_issue_logs(session: AsyncSession = Depends(get_db_session)) -> list[IssueLogRead]:
    logs = await issue_log_service.list_logs(session)
    return [IssueLogRead.model_validate(item) for item in logs]
