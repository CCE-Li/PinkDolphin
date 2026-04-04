from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import require_admin_token
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter(dependencies=[Depends(require_admin_token)])
dashboard_service = DashboardService()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(session: AsyncSession = Depends(get_db_session)) -> DashboardSummary:
    return await dashboard_service.get_summary(session)

