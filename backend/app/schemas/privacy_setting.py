from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class PrivacySettingUpdate(BaseModel):
    skip_url_on_sender_allowlist: bool
    skip_attachment_on_sender_allowlist: bool
    skip_llm_on_sender_allowlist: bool


class PrivacySettingRead(TimestampedSchema):
    skip_url_on_sender_allowlist: bool
    skip_attachment_on_sender_allowlist: bool
    skip_llm_on_sender_allowlist: bool
