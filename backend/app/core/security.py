from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.exceptions import AppException

bearer_scheme = HTTPBearer(auto_error=False)


def require_admin_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    settings = get_settings()
    if credentials is None or credentials.credentials != settings.admin_bearer_token:
        raise AppException(status_code=401, code="unauthorized", message="Invalid bearer token")
    return credentials.credentials

