from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import require_admin_token
from app.schemas.privacy_setting import PrivacySettingRead, PrivacySettingUpdate
from app.services.privacy_setting_service import PrivacySettingService

router = APIRouter(dependencies=[Depends(require_admin_token)])
privacy_setting_service = PrivacySettingService()


@router.get("", response_model=PrivacySettingRead)
async def get_privacy_settings(session: AsyncSession = Depends(get_db_session)) -> PrivacySettingRead:
    item = await privacy_setting_service.get_settings(session)
    return PrivacySettingRead.model_validate(item)


@router.put("", response_model=PrivacySettingRead)
async def update_privacy_settings(
    payload: PrivacySettingUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> PrivacySettingRead:
    item = await privacy_setting_service.update_settings(session, payload)
    return PrivacySettingRead.model_validate(item)
