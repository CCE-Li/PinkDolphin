from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.privacy_setting import PrivacySetting
from app.schemas.privacy_setting import PrivacySettingUpdate


class PrivacySettingService:
    async def get_settings(self, session: AsyncSession) -> PrivacySetting:
        item = (await session.execute(select(PrivacySetting).limit(1))).scalar_one_or_none()
        if item is None:
            defaults = get_settings()
            item = PrivacySetting(
                skip_url_on_sender_allowlist=defaults.privacy_skip_url_on_sender_allowlist,
                skip_attachment_on_sender_allowlist=defaults.privacy_skip_attachment_on_sender_allowlist,
                skip_llm_on_sender_allowlist=defaults.privacy_skip_llm_on_sender_allowlist,
            )
            session.add(item)
            await session.flush()
        return item

    async def update_settings(self, session: AsyncSession, payload: PrivacySettingUpdate) -> PrivacySetting:
        item = await self.get_settings(session)
        item.skip_url_on_sender_allowlist = payload.skip_url_on_sender_allowlist
        item.skip_attachment_on_sender_allowlist = payload.skip_attachment_on_sender_allowlist
        item.skip_llm_on_sender_allowlist = payload.skip_llm_on_sender_allowlist
        await session.flush()
        return item
