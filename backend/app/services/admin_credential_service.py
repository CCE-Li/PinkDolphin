from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.admin_credential import AdminCredential
from app.schemas.auth import ChangePasswordRequest
from app.utils.passwords import hash_password, verify_password


class AdminCredentialService:
    async def get_or_create_default(self, session: AsyncSession) -> AdminCredential:
        credential = (await session.execute(select(AdminCredential).limit(1))).scalar_one_or_none()
        if credential is None:
            credential = AdminCredential(username="admin", password_hash=hash_password("admin123"))
            session.add(credential)
            await session.flush()
        return credential

    async def verify_login(self, session: AsyncSession, username: str, password: str) -> AdminCredential:
        credential = await self.get_or_create_default(session)
        if credential.username != username or not verify_password(password, credential.password_hash):
            raise AppException(status_code=401, code="invalid_credentials", message="Invalid username or password")
        return credential

    async def change_credentials(self, session: AsyncSession, payload: ChangePasswordRequest) -> AdminCredential:
        credential = await self.verify_login(session, payload.current_username, payload.current_password)
        new_username = payload.new_username.strip()
        if not new_username:
            raise AppException(status_code=400, code="invalid_username", message="Username is required")
        if len(payload.new_password) < 6:
            raise AppException(status_code=400, code="invalid_password", message="Password must be at least 6 characters")
        credential.username = new_username
        credential.password_hash = hash_password(payload.new_password)
        await session.flush()
        return credential
