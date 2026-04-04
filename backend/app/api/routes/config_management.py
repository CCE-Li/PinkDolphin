from fastapi import APIRouter, Depends

from app.core.security import require_admin_token
from app.schemas.config_management import EnvFileRead, EnvFileUpdate
from app.services.config_management_service import ConfigManagementService

router = APIRouter(dependencies=[Depends(require_admin_token)])
config_management_service = ConfigManagementService()


@router.get("/env", response_model=EnvFileRead)
async def get_env_file() -> EnvFileRead:
    return config_management_service.read_env_file()


@router.put("/env", response_model=EnvFileRead)
async def update_env_file(payload: EnvFileUpdate) -> EnvFileRead:
    return config_management_service.write_env_file(payload.content)
