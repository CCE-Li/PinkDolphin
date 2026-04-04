from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import require_admin_token
from app.schemas.allowlist import AllowlistCreate, AllowlistRead, AllowlistUpdate
from app.services.allowlist_service import AllowlistService

router = APIRouter(dependencies=[Depends(require_admin_token)])
allowlist_service = AllowlistService()


@router.get("", response_model=list[AllowlistRead])
async def list_allowlists(session: AsyncSession = Depends(get_db_session)) -> list[AllowlistRead]:
    items = await allowlist_service.list_entries(session)
    return [AllowlistRead.model_validate(item) for item in items]


@router.post("", response_model=AllowlistRead)
async def create_allowlist(
    payload: AllowlistCreate,
    session: AsyncSession = Depends(get_db_session),
) -> AllowlistRead:
    item = await allowlist_service.create_entry(session, payload)
    return AllowlistRead.model_validate(item)


@router.put("/{entry_id}", response_model=AllowlistRead)
async def update_allowlist(
    entry_id: str,
    payload: AllowlistUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> AllowlistRead:
    entry = await allowlist_service.get_entry(session, entry_id)
    updated = await allowlist_service.update_entry(session, entry, payload)
    return AllowlistRead.model_validate(updated)
