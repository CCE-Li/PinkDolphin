from fastapi import APIRouter, Depends

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.config import get_settings
from app.core.security import require_admin_token
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse
from app.services.admin_credential_service import AdminCredentialService

router = APIRouter()
admin_credential_service = AdminCredentialService()


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)) -> LoginResponse:
    settings = get_settings()
    credential = await admin_credential_service.verify_login(session, payload.username, payload.password)
    return LoginResponse(access_token=settings.admin_bearer_token, username=credential.username)


@router.post("/change-password", response_model=LoginResponse, dependencies=[Depends(require_admin_token)])
async def change_password(
    payload: ChangePasswordRequest,
    session: AsyncSession = Depends(get_db_session),
) -> LoginResponse:
    settings = get_settings()
    credential = await admin_credential_service.change_credentials(session, payload)
    return LoginResponse(access_token=settings.admin_bearer_token, username=credential.username)
