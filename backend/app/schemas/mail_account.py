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
    listener_mode: str = "polling"

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
    listener_mode: str | None = None


class MailboxFolderRead(BaseModel):
    name: str
    label: str
    is_primary: bool
    last_seen_uid: int | None = None
    last_synced_uid: int | None = None
    last_sync_at: datetime | None = None


class MailProviderPresetRead(BaseModel):
    id: MailboxProvider
    label: str
    imap_host: str
    imap_port: int
    auth_type: str = "password"
    sync_mode: str = "imap"
    auth_hint: str
    password_placeholder: str
    supports_app_password: bool
    suggested_folders: list[str]


class OutlookOAuthStartRequest(BaseModel):
    owner_email: str | None = None
    display_name: str | None = None
    mailbox_folder: str = "INBOX"
    is_active: bool = True
    listen_interval_seconds: int | None = None
    listener_mode: str = "polling"


class OutlookOAuthStartResponse(BaseModel):
    authorization_url: str


class MailAccountRead(TimestampedSchema):
    owner_email: str
    email_address: str
    display_name: str | None
    provider: MailboxProvider
    auth_type: str = "password"
    sync_mode: str = "imap"
    provider_label: str
    imap_host: str
    imap_port: int
    imap_username: str
    mailbox_folder: str
    use_ssl: bool
    is_active: bool
    status: MailboxStatus
    listen_interval_seconds: int
    listener_mode: str = "polling"
    last_seen_uid: int | None
    last_synced_uid: int | None
    last_sync_at: datetime | None
    last_error: str | None
    auth_hint: str
    supports_app_password: bool
    suggested_folders: list[str]
    folders: list[MailboxFolderRead]
    graph_connected: bool = False


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
