from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import MailboxProvider, MailboxStatus
from app.schemas.common import TimestampedSchema


class MailAccountBase(BaseModel):
    owner_email: str | None = None
    email_address: str
    display_name: str | None = None
    provider: MailboxProvider = MailboxProvider.QQ
    imap_host: str | None = None
    imap_port: int | None = None
    imap_username: str | None = None
    mailbox_folder: str = "INBOX"
    use_ssl: bool = True
    is_active: bool = True
    listen_interval_seconds: int | None = None

    @field_validator("imap_host", mode="before")
    @classmethod
    def normalize_host(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class MailAccountCreate(MailAccountBase):
    imap_password: str = Field(min_length=1)


class MailAccountUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_email: str | None = None
    email_address: str | None = None
    display_name: str | None = None
    provider: MailboxProvider | None = None
    imap_host: str | None = None
    imap_port: int | None = None
    imap_username: str | None = None
    imap_password: str | None = None
    mailbox_folder: str | None = None
    use_ssl: bool | None = None
    is_active: bool | None = None
    listen_interval_seconds: int | None = None


class MailAccountRead(TimestampedSchema):
    owner_email: str
    email_address: str
    display_name: str | None
    provider: MailboxProvider
    imap_host: str
    imap_port: int
    imap_username: str
    mailbox_folder: str
    use_ssl: bool
    is_active: bool
    status: MailboxStatus
    listen_interval_seconds: int
    last_seen_uid: int | None
    last_synced_uid: int | None
    last_sync_at: datetime | None
    last_error: str | None


class MailAccountTestResult(BaseModel):
    ok: bool
    message: str
    mailbox_exists: bool
    highest_uid: int | None = None


class MailAccountSyncResult(BaseModel):
    queued: int
    synced: int = 0
    highest_uid: int | None = None
    account_id: str
