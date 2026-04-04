from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.integrations.imap import IMAPClient
from app.models.email import Email
from app.models.mailbox_sync_cursor import MailboxSyncCursor
from app.models.enums import IssueSeverity, MailboxProvider, MailboxStatus
from app.models.mail_account import MailAccount
from app.schemas.mail_account import MailAccountCreate, MailAccountTestResult, MailAccountUpdate
from app.services.issue_log_service import IssueLogService
from app.utils.crypto import decrypt_secret, encrypt_secret


@dataclass(slots=True)
class RuntimeMailAccount:
    id: str
    owner_email: str
    email_address: str
    provider: MailboxProvider
    imap_host: str
    imap_port: int
    imap_username: str
    imap_password: str
    mailbox_folder: str
    use_ssl: bool
    listen_interval_seconds: int
    connect_timeout_seconds: int
    mailbox_folder: str
    last_seen_uid: int | None


class MailAccountService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.imap_client = IMAPClient()
        self.issue_log_service = IssueLogService()
        self.provider_defaults: dict[MailboxProvider, dict[str, int | str]] = {
            MailboxProvider.QQ: {"imap_host": "imap.qq.com", "imap_port": 993},
            MailboxProvider.GMAIL: {"imap_host": "imap.gmail.com", "imap_port": 993},
            MailboxProvider.OUTLOOK: {"imap_host": "outlook.office365.com", "imap_port": 993},
            MailboxProvider.NETEASE_163: {"imap_host": "imap.163.com", "imap_port": 993},
            MailboxProvider.ALIYUN: {"imap_host": "imap.aliyun.com", "imap_port": 993},
        }

    async def list_accounts(self, session: AsyncSession) -> list[MailAccount]:
        await self.cleanup_missing_mailbox_emails(session)
        result = await session.execute(select(MailAccount).order_by(MailAccount.created_at.desc()))
        return list(result.scalars().all())

    async def list_active_accounts(self, session: AsyncSession) -> list[MailAccount]:
        result = await session.execute(select(MailAccount).where(MailAccount.is_active.is_(True)))
        return list(result.scalars().all())

    async def get_account(self, session: AsyncSession, account_id: str) -> MailAccount:
        account = await session.get(MailAccount, account_id)
        if account is None:
            raise AppException(status_code=404, code="mail_account_not_found", message="Mail account not found")
        return account

    async def create_account(self, session: AsyncSession, payload: MailAccountCreate) -> MailAccount:
        await self._ensure_email_not_exists(session, payload.email_address)
        normalized = self._normalize_payload(payload.model_dump())
        account = MailAccount(
            **normalized,
            imap_password=encrypt_secret(payload.imap_password),
            status=MailboxStatus.IDLE if normalized["is_active"] else MailboxStatus.DISABLED,
            connect_timeout_seconds=20,
        )
        session.add(account)
        await session.flush()
        await self.initialize_cursor_from_current_mailbox(session, account)
        return account

    async def update_account(self, session: AsyncSession, account: MailAccount, payload: MailAccountUpdate) -> MailAccount:
        changes = payload.model_dump(exclude_unset=True)
        if "email_address" in changes and changes["email_address"] != account.email_address:
            await self._ensure_email_not_exists(session, str(changes["email_address"]))
        normalized = self._normalize_payload({**account.__dict__, **changes}, is_update=True)
        for field in (
            "owner_email",
            "email_address",
            "display_name",
            "provider",
            "imap_host",
            "imap_port",
            "imap_username",
            "mailbox_folder",
            "use_ssl",
            "is_active",
            "listen_interval_seconds",
        ):
            if field in normalized:
                setattr(account, field, normalized[field])
        if payload.imap_password:
            account.imap_password = encrypt_secret(payload.imap_password)
        account.status = MailboxStatus.IDLE if account.is_active else MailboxStatus.DISABLED
        if not account.is_active:
            account.last_error = None
        await session.flush()
        if self._requires_cursor_reset(changes):
            await self.initialize_cursor_from_current_mailbox(session, account)
        return account

    async def test_connection(self, session: AsyncSession, account: MailAccount) -> MailAccountTestResult:
        runtime = self.to_runtime(account)
        try:
            highest_uid = await self._test_runtime_account(runtime)
            account.last_error = None
            if account.is_active:
                account.status = MailboxStatus.IDLE
            await session.flush()
            return MailAccountTestResult(
                ok=True,
                message="IMAP connection succeeded",
                mailbox_exists=True,
                highest_uid=highest_uid,
            )
        except Exception as exc:
            account.status = MailboxStatus.ERROR
            account.last_error = str(exc)
            await self.issue_log_service.log(
                session,
                component="mail_account:test_connection",
                severity=IssueSeverity.ERROR,
                message="IMAP connection test failed",
                details={
                    "account_id": account.id,
                    "email_address": account.email_address,
                    "provider": account.provider.value,
                    "error": str(exc),
                },
            )
            await session.flush()
            return MailAccountTestResult(
                ok=False,
                message=str(exc),
                mailbox_exists=False,
                highest_uid=None,
            )

    def to_runtime(self, account: MailAccount) -> RuntimeMailAccount:
        return RuntimeMailAccount(
            id=account.id,
            owner_email=account.owner_email,
            email_address=account.email_address,
            provider=account.provider,
            imap_host=account.imap_host,
            imap_port=account.imap_port,
            imap_username=account.imap_username,
            imap_password=decrypt_secret(account.imap_password),
            use_ssl=account.use_ssl,
            listen_interval_seconds=account.listen_interval_seconds,
            connect_timeout_seconds=account.connect_timeout_seconds,
            mailbox_folder=account.mailbox_folder,
            last_seen_uid=account.last_seen_uid,
        )

    async def hydrate_account_progress(self, session: AsyncSession, account: MailAccount) -> MailAccount:
        cursor = await self.get_or_create_cursor(session, account.id, account.mailbox_folder)
        account.last_seen_uid = cursor.last_seen_uid
        account.last_synced_uid = cursor.last_synced_uid
        account.last_sync_at = cursor.last_sync_at
        return account

    async def get_or_create_cursor(
        self,
        session: AsyncSession,
        account_id: str,
        mailbox_folder: str,
    ) -> MailboxSyncCursor:
        stmt = select(MailboxSyncCursor).where(
            MailboxSyncCursor.mail_account_id == account_id,
            MailboxSyncCursor.mailbox_folder == mailbox_folder,
        )
        cursor = (await session.execute(stmt)).scalar_one_or_none()
        if cursor is None:
            cursor = MailboxSyncCursor(mail_account_id=account_id, mailbox_folder=mailbox_folder)
            session.add(cursor)
            await session.flush()
        return cursor

    async def mark_listening(self, session: AsyncSession, account_id: str) -> None:
        account = await self.get_account(session, account_id)
        if account.is_active:
            account.status = MailboxStatus.LISTENING
            account.last_error = None
            await session.flush()

    async def mark_error(self, session: AsyncSession, account_id: str, error: str) -> None:
        account = await self.get_account(session, account_id)
        account.status = MailboxStatus.ERROR
        account.last_error = error
        await self.issue_log_service.log(
            session,
            component="mail_account:listener",
            severity=IssueSeverity.ERROR,
            message="Mailbox listener encountered an error",
            details={
                "account_id": account.id,
                "email_address": account.email_address,
                "provider": account.provider.value,
                "error": error,
            },
        )
        await session.flush()

    async def mark_seen(self, session: AsyncSession, account_id: str, highest_uid: int | None) -> None:
        if highest_uid is None:
            return
        account = await self.get_account(session, account_id)
        cursor = await self.get_or_create_cursor(session, account.id, account.mailbox_folder)
        cursor.last_seen_uid = max(cursor.last_seen_uid or 0, highest_uid)
        account.last_seen_uid = cursor.last_seen_uid
        account.last_synced_uid = cursor.last_synced_uid
        account.last_sync_at = cursor.last_sync_at
        account.last_error = None
        account.status = MailboxStatus.LISTENING if account.is_active else MailboxStatus.DISABLED
        await session.flush()

    async def mark_synced(self, session: AsyncSession, account_id: str, uid: int) -> None:
        account = await self.get_account(session, account_id)
        cursor = await self.get_or_create_cursor(session, account.id, account.mailbox_folder)
        cursor.last_synced_uid = max(cursor.last_synced_uid or 0, uid)
        cursor.last_sync_at = datetime.now(timezone.utc)
        account.last_seen_uid = cursor.last_seen_uid
        account.last_synced_uid = cursor.last_synced_uid
        account.last_sync_at = cursor.last_sync_at
        account.last_error = None
        if account.is_active:
            account.status = MailboxStatus.LISTENING
        await session.flush()

    async def initialize_cursor_from_current_mailbox(self, session: AsyncSession, account: MailAccount) -> int | None:
        highest_uid: int | None = None
        runtime = self.to_runtime(account)
        try:
            highest_uid = await self._test_runtime_account(runtime)
            cursor = await self.get_or_create_cursor(session, account.id, account.mailbox_folder)
            cursor.last_seen_uid = highest_uid
            cursor.last_synced_uid = highest_uid
            cursor.last_sync_at = datetime.now(timezone.utc) if highest_uid is not None else cursor.last_sync_at
            account.last_seen_uid = highest_uid
            account.last_synced_uid = highest_uid
            account.last_sync_at = cursor.last_sync_at
            account.last_error = None
            if account.is_active:
                account.status = MailboxStatus.IDLE
            await session.flush()
        except Exception as exc:
            account.last_error = str(exc)
            account.status = MailboxStatus.ERROR
            await self.issue_log_service.log(
                session,
                component="mail_account:initialize_cursor",
                severity=IssueSeverity.ERROR,
                message="Failed to initialize mailbox cursor from current UID",
                details={
                    "account_id": account.id,
                    "email_address": account.email_address,
                    "provider": account.provider.value,
                    "error": str(exc),
                },
            )
            await session.flush()
            raise
        return highest_uid

    async def delete_account(self, session: AsyncSession, account: MailAccount) -> int:
        from app.services.email_service import EmailService

        await session.refresh(account, attribute_names=["emails"])
        deleted_count = await EmailService().delete_emails_by_mail_account_id(session, account.id)
        await session.delete(account)
        await session.flush()
        await self.issue_log_service.log(
            session,
            component="mail_account:delete",
            severity=IssueSeverity.INFO,
            message="Mail account deleted with local mailbox emails",
            details={
                "account_id": account.id,
                "email_address": account.email_address,
                "deleted_email_count": deleted_count,
            },
        )
        return deleted_count

    async def cleanup_missing_mailbox_emails(self, session: AsyncSession) -> int:
        from app.services.email_service import EmailService

        stmt = (
            select(Email)
            .where(Email.mailbox_account_id.is_not(None))
            .options(selectinload(Email.mail_account))
            .order_by(Email.created_at.desc())
        )
        emails = list((await session.execute(stmt)).scalars().all())
        deleted_count = 0
        email_service = EmailService()
        for email in emails:
            if email.mail_account is not None:
                continue
            await email_service.delete_email(session, email, delete_remote=False)
            deleted_count += 1
        return deleted_count

    async def _ensure_email_not_exists(self, session: AsyncSession, email_address: str) -> None:
        stmt = select(MailAccount.id).where(MailAccount.email_address == email_address.lower())
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            raise AppException(status_code=409, code="mail_account_exists", message="Mail account already exists")

    async def _test_runtime_account(self, runtime: RuntimeMailAccount) -> int | None:
        import asyncio

        client = await asyncio.to_thread(self.imap_client.connect, runtime)
        try:
            return await asyncio.to_thread(self.imap_client.get_highest_uid, client)
        finally:
            await asyncio.to_thread(self.imap_client.close, client)

    def _normalize_payload(self, payload: dict, *, is_update: bool = False) -> dict:
        provider = MailboxProvider(payload.get("provider") or MailboxProvider.QQ)
        email_address = str(payload.get("email_address") or "").strip().lower()
        owner_email = str(payload.get("owner_email") or email_address).strip().lower()
        username = str(payload.get("imap_username") or email_address).strip()
        host = payload.get("imap_host")
        port = payload.get("imap_port")
        listen_interval_seconds = payload.get("listen_interval_seconds")

        if provider in self.provider_defaults:
            defaults = self.provider_defaults[provider]
            host = host or defaults["imap_host"]
            port = int(port or defaults["imap_port"])
        else:
            if not host and not is_update:
                raise AppException(status_code=400, code="imap_host_required", message="imap_host is required")
            if not port and not is_update:
                raise AppException(status_code=400, code="imap_port_required", message="imap_port is required")
            port = int(port or 993)

        listen_interval_seconds = int(listen_interval_seconds or self.settings.mailbox_default_poll_seconds)
        if listen_interval_seconds < 3:
            raise AppException(
                status_code=400,
                code="invalid_listen_interval",
                message="listen_interval_seconds must be at least 3",
            )

        return {
            "owner_email": owner_email,
            "email_address": email_address,
            "display_name": payload.get("display_name"),
            "provider": provider,
            "imap_host": str(host).strip(),
            "imap_port": port,
            "imap_username": username,
            "mailbox_folder": str(payload.get("mailbox_folder") or "INBOX").strip(),
            "use_ssl": bool(payload.get("use_ssl", True)),
            "is_active": bool(payload.get("is_active", True)),
            "listen_interval_seconds": listen_interval_seconds,
        }

    @staticmethod
    def _requires_cursor_reset(changes: dict) -> bool:
        reset_fields = {
            "email_address",
            "provider",
            "imap_host",
            "imap_port",
            "imap_username",
            "imap_password",
            "mailbox_folder",
            "use_ssl",
        }
        return any(field in changes for field in reset_fields)
