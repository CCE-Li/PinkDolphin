from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.integrations.graph_mail import GraphMailClient
from app.integrations.imap import IMAPClient
from app.models.email import Email
from app.models.mailbox_sync_cursor import MailboxSyncCursor
from app.models.enums import IssueSeverity, MailboxProvider, MailboxStatus
from app.models.mail_account import MailAccount
from app.schemas.mail_account import (
    MailAccountCreate,
    MailAccountRead,
    MailAccountTestResult,
    MailAccountUpdate,
    MailProviderPresetRead,
    MailboxFolderRead,
    OutlookOAuthStartRequest,
)
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
    listener_mode: str
    connect_timeout_seconds: int
    last_seen_uid: int | None
    auth_type: str
    sync_mode: str
    oauth_access_token: str | None
    oauth_refresh_token: str | None
    oauth_token_expires_at: datetime | None
    graph_delta_link: str | None


@dataclass(frozen=True, slots=True)
class ProviderPreset:
    label: str
    imap_host: str
    imap_port: int
    auth_type: str
    sync_mode: str
    auth_hint: str
    password_placeholder: str
    supports_app_password: bool
    suggested_folders: tuple[str, ...]


class MailAccountService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.imap_client = IMAPClient()
        self.graph_client = GraphMailClient()
        self.issue_log_service = IssueLogService()
        self.provider_defaults: dict[MailboxProvider, ProviderPreset] = {
            MailboxProvider.QQ: ProviderPreset(
                label="QQ 邮箱",
                imap_host="imap.qq.com",
                imap_port=993,
                auth_type="password",
                sync_mode="imap",
                auth_hint="开启 IMAP 后使用客户端授权码登录。",
                password_placeholder="QQ 邮箱 IMAP 授权码",
                supports_app_password=True,
                suggested_folders=("INBOX", "Sent", "Drafts", "Spam"),
            ),
            MailboxProvider.GMAIL: ProviderPreset(
                label="Gmail",
                imap_host="imap.gmail.com",
                imap_port=993,
                auth_type="password",
                sync_mode="imap",
                auth_hint="建议开启两步验证后使用应用专用密码。",
                password_placeholder="Gmail 应用专用密码",
                supports_app_password=True,
                suggested_folders=("INBOX", "[Gmail]/Sent Mail", "[Gmail]/Drafts", "[Gmail]/Spam"),
            ),
            MailboxProvider.OUTLOOK: ProviderPreset(
                label="Outlook / Microsoft 365",
                imap_host="graph.microsoft.com",
                imap_port=443,
                auth_type="oauth2",
                sync_mode="graph",
                auth_hint="Outlook.com / Microsoft 365 通过 Microsoft Graph OAuth2 授权，不再使用 IMAP Basic Auth。",
                password_placeholder="通过 Microsoft 登录授权",
                supports_app_password=False,
                suggested_folders=("INBOX", "Sent Items", "Drafts", "Junk Email"),
            ),
            MailboxProvider.NETEASE_163: ProviderPreset(
                label="网易 163 邮箱",
                imap_host="imap.163.com",
                imap_port=993,
                auth_type="password",
                sync_mode="imap",
                auth_hint="需先开启 IMAP，并使用客户端授权密码。",
                password_placeholder="网易 163 邮箱客户端授权密码",
                supports_app_password=True,
                suggested_folders=("INBOX", "Sent", "Drafts", "Spam"),
            ),
            MailboxProvider.ALIYUN: ProviderPreset(
                label="阿里云邮箱",
                imap_host="imap.aliyun.com",
                imap_port=993,
                auth_type="password",
                sync_mode="imap",
                auth_hint="企业邮箱通常使用密码或客户端授权密码。",
                password_placeholder="阿里云邮箱密码或客户端授权密码",
                supports_app_password=True,
                suggested_folders=("INBOX", "Sent", "Drafts", "Spam"),
            ),
            MailboxProvider.CUSTOM: ProviderPreset(
                label="自定义 IMAP",
                imap_host="imap.example.com",
                imap_port=993,
                auth_type="password",
                sync_mode="imap",
                auth_hint="填写实际 IMAP 主机、端口和账号信息。",
                password_placeholder="IMAP 密码或授权码",
                supports_app_password=False,
                suggested_folders=("INBOX",),
            ),
        }

    async def list_accounts(self, session: AsyncSession) -> list[MailAccount]:
        await self.cleanup_missing_mailbox_emails(session)
        result = await session.execute(select(MailAccount).order_by(MailAccount.created_at.desc()))
        return list(result.scalars().all())

    def list_provider_presets(self) -> list[MailProviderPresetRead]:
        return [
            MailProviderPresetRead(
                id=provider,
                label=preset.label,
                imap_host=preset.imap_host,
                imap_port=preset.imap_port,
                auth_type=preset.auth_type,
                sync_mode=preset.sync_mode,
                auth_hint=preset.auth_hint,
                password_placeholder=preset.password_placeholder,
                supports_app_password=preset.supports_app_password,
                suggested_folders=list(preset.suggested_folders),
            )
            for provider, preset in self.provider_defaults.items()
        ]

    async def list_active_accounts(self, session: AsyncSession) -> list[MailAccount]:
        result = await session.execute(select(MailAccount).where(MailAccount.is_active.is_(True)))
        return list(result.scalars().all())

    async def get_account(self, session: AsyncSession, account_id: str) -> MailAccount:
        account = await session.get(MailAccount, account_id)
        if account is None:
            raise AppException(status_code=404, code="mail_account_not_found", message="Mail account not found")
        return account

    async def create_account(self, session: AsyncSession, payload: MailAccountCreate) -> MailAccount:
        if payload.provider == MailboxProvider.OUTLOOK:
            raise AppException(status_code=400, code="outlook_requires_oauth", message="Outlook accounts must be connected through Microsoft Graph OAuth")
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
        await session.refresh(account)
        return account

    async def update_account(self, session: AsyncSession, account: MailAccount, payload: MailAccountUpdate) -> MailAccount:
        if (payload.provider == MailboxProvider.OUTLOOK or account.provider == MailboxProvider.OUTLOOK) and account.sync_mode == "graph":
            raise AppException(status_code=400, code="outlook_requires_oauth", message="Outlook Graph accounts should be reauthorized instead of edited as IMAP")
        changes = payload.model_dump(exclude_unset=True)
        if "email_address" in changes and changes["email_address"] != account.email_address:
            await self._ensure_email_not_exists(session, str(changes["email_address"]))
        normalized = self._normalize_payload({**account.__dict__, **changes}, is_update=True)
        for field in (
            "owner_email",
            "email_address",
            "display_name",
            "provider",
            "auth_type",
            "sync_mode",
            "imap_host",
            "imap_port",
            "imap_username",
            "mailbox_folder",
            "use_ssl",
            "is_active",
            "listen_interval_seconds",
            "listener_mode",
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
        await session.refresh(account)
        return account

    async def test_connection(self, session: AsyncSession, account: MailAccount) -> MailAccountTestResult:
        runtime = self.to_runtime(account)
        try:
            highest_uid = await self._test_runtime_account(runtime)
            preset = self._get_provider_preset(account.provider)
            account.last_error = None
            if account.is_active:
                account.status = MailboxStatus.IDLE
            await session.flush()
            return MailAccountTestResult(
                ok=True,
                message=f"{preset.label} {'Graph' if runtime.sync_mode == 'graph' else 'IMAP'} 连接成功",
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
            listener_mode=account.listener_mode,
            connect_timeout_seconds=account.connect_timeout_seconds,
            last_seen_uid=account.last_seen_uid,
            mailbox_folder=account.mailbox_folder,
            auth_type=account.auth_type,
            sync_mode=account.sync_mode,
            oauth_access_token=decrypt_secret(account.oauth_access_token) if account.oauth_access_token else None,
            oauth_refresh_token=decrypt_secret(account.oauth_refresh_token) if account.oauth_refresh_token else None,
            oauth_token_expires_at=account.oauth_token_expires_at,
            graph_delta_link=account.graph_delta_link,
        )

    async def hydrate_account_progress(self, session: AsyncSession, account: MailAccount) -> MailAccount:
        cursor = await self.get_or_create_cursor(session, account.id, account.mailbox_folder)
        account.last_seen_uid = cursor.last_seen_uid
        account.last_synced_uid = cursor.last_synced_uid
        account.last_sync_at = cursor.last_sync_at
        return account

    async def to_read_model(self, session: AsyncSession, account: MailAccount) -> MailAccountRead:
        preset = self._get_provider_preset(account.provider)
        folders = await self.list_folder_states(session, account)
        return MailAccountRead(
            id=account.id,
            created_at=account.created_at,
            updated_at=account.updated_at,
            owner_email=account.owner_email,
            email_address=account.email_address,
            display_name=account.display_name,
            provider=account.provider,
            auth_type=account.auth_type,
            sync_mode=account.sync_mode,
            provider_label=preset.label,
            imap_host=account.imap_host,
            imap_port=account.imap_port,
            imap_username=account.imap_username,
            mailbox_folder=account.mailbox_folder,
            use_ssl=account.use_ssl,
            is_active=account.is_active,
            status=account.status,
            listen_interval_seconds=account.listen_interval_seconds,
            listener_mode=account.listener_mode,
            last_seen_uid=account.last_seen_uid,
            last_synced_uid=account.last_synced_uid,
            last_sync_at=account.last_sync_at,
            last_error=account.last_error,
            auth_hint=preset.auth_hint,
            supports_app_password=preset.supports_app_password,
            suggested_folders=list(preset.suggested_folders),
            folders=folders,
            graph_connected=bool(account.oauth_refresh_token or account.oauth_access_token),
        )

    async def list_folder_states(self, session: AsyncSession, account: MailAccount) -> list[MailboxFolderRead]:
        stmt = (
            select(MailboxSyncCursor)
            .where(MailboxSyncCursor.mail_account_id == account.id)
            .order_by(MailboxSyncCursor.mailbox_folder.asc())
        )
        cursor_rows = list((await session.execute(stmt)).scalars().all())
        folders_by_name = {
            row.mailbox_folder: MailboxFolderRead(
                name=row.mailbox_folder,
                label=self._format_folder_label(row.mailbox_folder),
                is_primary=row.mailbox_folder == account.mailbox_folder,
                last_seen_uid=row.last_seen_uid,
                last_synced_uid=row.last_synced_uid,
                last_sync_at=row.last_sync_at,
            )
            for row in cursor_rows
        }
        if account.mailbox_folder not in folders_by_name:
            folders_by_name[account.mailbox_folder] = MailboxFolderRead(
                name=account.mailbox_folder,
                label=self._format_folder_label(account.mailbox_folder),
                is_primary=True,
                last_seen_uid=account.last_seen_uid,
                last_synced_uid=account.last_synced_uid,
                last_sync_at=account.last_sync_at,
            )

        ordered_names = [account.mailbox_folder]
        for folder in self._get_provider_preset(account.provider).suggested_folders:
            if folder not in ordered_names:
                ordered_names.append(folder)
        for folder in sorted(folders_by_name):
            if folder not in ordered_names:
                ordered_names.append(folder)

        result: list[MailboxFolderRead] = []
        for folder_name in ordered_names:
            folder = folders_by_name.get(folder_name)
            if folder is not None:
                result.append(folder)
                continue
            result.append(
                MailboxFolderRead(
                    name=folder_name,
                    label=self._format_folder_label(folder_name),
                    is_primary=folder_name == account.mailbox_folder,
                )
            )
        return result

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
            cursor = await self.get_or_create_cursor(session, account.id, account.mailbox_folder)
            if runtime.sync_mode == "graph":
                access_token = await self.get_graph_access_token(runtime)
                delta_result = await self.graph_client.delta_messages(access_token, delta_link=None, folder_name="inbox")
                account.graph_delta_link = delta_result.delta_link
                cursor.last_seen_uid = cursor.last_seen_uid or 0
                cursor.last_synced_uid = cursor.last_synced_uid or 0
                cursor.last_sync_at = datetime.now(timezone.utc)
                account.last_seen_uid = cursor.last_seen_uid
                account.last_synced_uid = cursor.last_synced_uid
                account.last_sync_at = cursor.last_sync_at
            else:
                highest_uid = await self._test_runtime_account(runtime)
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

    async def start_outlook_oauth(self, payload: OutlookOAuthStartRequest) -> str:
        state = encrypt_secret(
            json.dumps(
                {
                    "provider": MailboxProvider.OUTLOOK.value,
                    "owner_email": (payload.owner_email or "").strip().lower() or None,
                    "display_name": (payload.display_name or "").strip() or None,
                    "mailbox_folder": (payload.mailbox_folder or "INBOX").strip() or "INBOX",
                    "is_active": payload.is_active,
                    "listen_interval_seconds": payload.listen_interval_seconds,
                    "listener_mode": payload.listener_mode,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
        )
        return self.graph_client.build_authorization_url(state)

    async def complete_outlook_oauth(self, session: AsyncSession, *, code: str, state: str) -> MailAccount:
        payload = self._decode_oauth_state(state)
        token_bundle = await self.graph_client.exchange_code(code)
        profile = await self.graph_client.get_profile(token_bundle.access_token)
        existing = (
            await session.execute(select(MailAccount).where(MailAccount.email_address == profile.email_address))
        ).scalar_one_or_none()
        if existing is not None and existing.provider != MailboxProvider.OUTLOOK:
            raise AppException(status_code=409, code="mail_account_exists", message="A non-Outlook account with the same email already exists")
        preset = self._get_provider_preset(MailboxProvider.OUTLOOK)
        normalized = self._normalize_payload(
            {
                "owner_email": payload.get("owner_email") or profile.email_address,
                "email_address": profile.email_address,
                "display_name": payload.get("display_name") or profile.display_name,
                "provider": MailboxProvider.OUTLOOK,
                "imap_host": preset.imap_host,
                "imap_port": preset.imap_port,
                "imap_username": profile.email_address,
                "mailbox_folder": payload.get("mailbox_folder") or "INBOX",
                "use_ssl": True,
                    "is_active": payload.get("is_active", True),
                    "listen_interval_seconds": payload.get("listen_interval_seconds"),
                    "listener_mode": payload.get("listener_mode", "polling"),
                }
            )
        target = existing
        if target is None:
            target = MailAccount(
                **normalized,
                imap_password=encrypt_secret("oauth2"),
                status=MailboxStatus.IDLE if normalized["is_active"] else MailboxStatus.DISABLED,
                connect_timeout_seconds=20,
            )
            session.add(target)
            await session.flush()
        else:
            for field in (
                "owner_email",
                "email_address",
                "display_name",
                "provider",
                "auth_type",
                "sync_mode",
                "imap_host",
                "imap_port",
                "imap_username",
                "mailbox_folder",
                "use_ssl",
                "is_active",
                "listen_interval_seconds",
                "listener_mode",
            ):
                setattr(target, field, normalized[field])
            target.status = MailboxStatus.IDLE if target.is_active else MailboxStatus.DISABLED
            target.last_error = None
        target.oauth_access_token = encrypt_secret(token_bundle.access_token)
        target.oauth_refresh_token = encrypt_secret(token_bundle.refresh_token) if token_bundle.refresh_token else None
        target.oauth_token_expires_at = token_bundle.expires_at
        target.oauth_scope = token_bundle.scope
        target.oauth_subject = profile.subject
        target.graph_delta_link = None
        await session.flush()
        await self.initialize_cursor_from_current_mailbox(session, target)
        return target

    async def get_graph_access_token(self, runtime: RuntimeMailAccount) -> str:
        if runtime.sync_mode != "graph":
            raise AppException(status_code=400, code="graph_not_enabled", message="This account does not use Microsoft Graph")
        if runtime.oauth_access_token and runtime.oauth_token_expires_at and runtime.oauth_token_expires_at > datetime.now(timezone.utc):
            return runtime.oauth_access_token
        if not runtime.oauth_refresh_token:
            raise AppException(status_code=401, code="graph_refresh_token_missing", message="Outlook account requires reauthorization")
        token_bundle = await self.graph_client.refresh_access_token(runtime.oauth_refresh_token)
        await self.update_graph_tokens(runtime.id, token_bundle.access_token, token_bundle.refresh_token, token_bundle.expires_at, token_bundle.scope)
        return token_bundle.access_token

    async def update_graph_tokens(
        self,
        account_id: str,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime,
        scope: str | None,
    ) -> None:
        from app.db.session import db_manager

        async with db_manager.session() as session:
            account = await self.get_account(session, account_id)
            account.oauth_access_token = encrypt_secret(access_token)
            if refresh_token:
                account.oauth_refresh_token = encrypt_secret(refresh_token)
            account.oauth_token_expires_at = expires_at
            account.oauth_scope = scope
            account.last_error = None
            await session.flush()

    async def update_graph_delta_link(self, session: AsyncSession, account_id: str, delta_link: str | None) -> None:
        account = await self.get_account(session, account_id)
        account.graph_delta_link = delta_link
        await session.flush()

    async def _test_runtime_account(self, runtime: RuntimeMailAccount) -> int | None:
        import asyncio

        if runtime.sync_mode == "graph":
            access_token = await self.get_graph_access_token(runtime)
            await self.graph_client.get_profile(access_token)
            return None

        client = await asyncio.to_thread(self.imap_client.connect, runtime)
        try:
            return await asyncio.to_thread(self.imap_client.get_highest_uid, client)
        finally:
            await asyncio.to_thread(self.imap_client.close, client)

    def _normalize_payload(self, payload: dict, *, is_update: bool = False) -> dict:
        provider = MailboxProvider(payload.get("provider") or MailboxProvider.QQ)
        preset = self._get_provider_preset(provider)
        email_address = str(payload.get("email_address") or "").strip().lower()
        owner_email = str(payload.get("owner_email") or email_address).strip().lower()
        username = str(payload.get("imap_username") or email_address).strip()
        host = payload.get("imap_host")
        port = payload.get("imap_port")
        listen_interval_seconds = payload.get("listen_interval_seconds")
        listener_mode = str(payload.get("listener_mode") or "polling").strip().lower()

        if provider in self.provider_defaults:
            host = host or preset.imap_host
            port = int(port or preset.imap_port)
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
        if listener_mode not in {"polling", "idle_fallback"}:
            raise AppException(
                status_code=400,
                code="invalid_listener_mode",
                message="listener_mode must be polling or idle_fallback",
            )

        return {
            "owner_email": owner_email,
            "email_address": email_address,
            "display_name": payload.get("display_name"),
            "provider": provider,
            "auth_type": preset.auth_type,
            "sync_mode": preset.sync_mode,
            "imap_host": str(host).strip(),
            "imap_port": port,
            "imap_username": username,
            "mailbox_folder": str(payload.get("mailbox_folder") or "INBOX").strip(),
            "use_ssl": bool(payload.get("use_ssl", True)),
            "is_active": bool(payload.get("is_active", True)),
            "listen_interval_seconds": listen_interval_seconds,
            "listener_mode": listener_mode,
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
            "listener_mode",
        }
        return any(field in changes for field in reset_fields)

    def _get_provider_preset(self, provider: MailboxProvider) -> ProviderPreset:
        return self.provider_defaults.get(provider) or self.provider_defaults[MailboxProvider.CUSTOM]

    @staticmethod
    def _format_folder_label(folder_name: str) -> str:
        mapping = {
            "INBOX": "Inbox",
            "Sent": "Sent",
            "Sent Items": "Sent",
            "Drafts": "Drafts",
            "Spam": "Spam",
            "Junk Email": "Junk",
            "[Gmail]/Sent Mail": "Sent",
            "[Gmail]/Drafts": "Drafts",
            "[Gmail]/Spam": "Spam",
        }
        return mapping.get(folder_name, folder_name)

    @staticmethod
    def _decode_oauth_state(state: str) -> dict:
        try:
            payload = json.loads(decrypt_secret(state))
        except Exception as exc:
            raise AppException(status_code=400, code="invalid_oauth_state", message="Invalid Outlook OAuth state") from exc
        created_at = payload.get("created_at")
        if not created_at:
            raise AppException(status_code=400, code="invalid_oauth_state", message="Outlook OAuth state is missing timestamp")
        age = datetime.now(timezone.utc) - datetime.fromisoformat(created_at)
        if age.total_seconds() > 900:
            raise AppException(status_code=400, code="oauth_state_expired", message="Outlook OAuth session expired")
        return payload

    def build_outlook_callback_redirect(self, *, success: bool, message: str, account_id: str | None = None) -> str:
        from urllib.parse import urlencode

        params = {"oauth": "outlook", "status": "success" if success else "error", "message": message}
        if account_id:
            params["account_id"] = account_id
        return f"{self.settings.frontend_app_url.rstrip('/')}/mailboxes?{urlencode(params)}"
