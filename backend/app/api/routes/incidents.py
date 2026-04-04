from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import require_admin_token
from app.schemas.incident import IncidentRead
from app.services.incident_service import IncidentService

router = APIRouter(dependencies=[Depends(require_admin_token)])
incident_service = IncidentService()


@router.get("", response_model=list[IncidentRead])
async def list_incidents(session: AsyncSession = Depends(get_db_session)) -> list[IncidentRead]:
    incidents = await incident_service.list_incidents(session)
    return [IncidentRead.model_validate(incident) for incident in incidents]

