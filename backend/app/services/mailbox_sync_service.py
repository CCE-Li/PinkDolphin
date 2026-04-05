from __future__ import annotations

import asyncio
import imaplib
from dataclasses import dataclass

from app.core.exceptions import AppException
from app.db.session import db_manager
from app.models.enums import AuditEventType, EmailSource
from app.services.email_service import EmailService
from app.services.mail_account_service import MailAccountService
from app.tasks.celery_app import celery_app


@dataclass(slots=True)
class MailboxSyncState:
    queued: int
    synced: int
    highest_uid: int | None
    active: bool
    poll_seconds: int


class MailboxSyncService:
    def __init__(self) -> None:
        self.mail_account_service = MailAccountService()
        self.email_service = EmailService()
        self.imap_client = self.mail_account_service.imap_client

    async def sync_account_once(
        self,
        account_id: str,
        *,
        client: imaplib.IMAP4 | None = None,
        process_inline: bool = False,
    ) -> MailboxSyncState:
        async with db_manager.session() as session:
            account = await self.mail_account_service.get_account(session, account_id)
            await self.mail_account_service.hydrate_account_progress(session, account)
            if not account.is_active:
                return MailboxSyncState(queued=0, synced=0, highest_uid=account.last_seen_uid, active=False, poll_seconds=0)
            runtime = self.mail_account_service.to_runtime(account)
            if runtime.provider.value == "qq" and not runtime.imap_username.endswith("@qq.com"):
                raise AppException(
                    status_code=400,
                    code="invalid_qq_imap_username",
                    message="QQ mailbox IMAP username should be the full QQ email address",
                )

        if runtime.sync_mode == "graph":
            return await self._sync_graph_account(runtime, process_inline=process_inline)

        owns_client = client is None
        if owns_client:
            client = await asyncio.to_thread(self.imap_client.connect, runtime)
        try:
            new_uids = await asyncio.to_thread(self.imap_client.search_since_uid, client, runtime.last_seen_uid)
            highest_uid = max(new_uids) if new_uids else runtime.last_seen_uid
            queued = 0
            synced = 0
            for uid in new_uids:
                raw_bytes = await asyncio.to_thread(self.imap_client.fetch_rfc822, client, uid)
                raw_email = raw_bytes.decode("utf-8", errors="replace")
                if process_inline:
                    await self.analyze_raw_email(
                        mail_account_id=runtime.id,
                        uid=uid,
                        raw_email=raw_email,
                        remote_folder=runtime.mailbox_folder,
                    )
                    synced += 1
                else:
                    celery_app.send_task(
                        "mailboxes.analyze_raw_email",
                        kwargs={
                            "mail_account_id": runtime.id,
                            "uid": uid,
                            "raw_email": raw_email,
                            "remote_folder": runtime.mailbox_folder,
                        },
                    )
                    queued += 1

            async with db_manager.session() as session:
                await self.mail_account_service.mark_seen(session, runtime.id, highest_uid)

            return MailboxSyncState(
                queued=queued,
                synced=synced,
                highest_uid=highest_uid,
                active=True,
                poll_seconds=runtime.listen_interval_seconds,
            )
        finally:
            if owns_client and client is not None:
                await asyncio.to_thread(self.imap_client.close, client)

    async def _sync_graph_account(
        self,
        runtime,
        *,
        process_inline: bool,
    ) -> MailboxSyncState:
        access_token = await self.mail_account_service.get_graph_access_token(runtime)
        delta_result = await self.mail_account_service.graph_client.delta_messages(
            access_token,
            delta_link=runtime.graph_delta_link,
            folder_name="inbox",
        )
        queued = 0
        synced = 0
        for message in delta_result.messages:
            remote_message_id = str(message["id"])
            raw_bytes = await self.mail_account_service.graph_client.fetch_message_mime(access_token, remote_message_id)
            raw_email = raw_bytes.decode("utf-8", errors="replace")
            if process_inline:
                await self.analyze_raw_email(
                    mail_account_id=runtime.id,
                    uid=None,
                    remote_message_id=remote_message_id,
                    raw_email=raw_email,
                    remote_folder=runtime.mailbox_folder,
                )
                synced += 1
            else:
                celery_app.send_task(
                    "mailboxes.analyze_raw_email",
                    kwargs={
                        "mail_account_id": runtime.id,
                        "uid": 0,
                        "remote_message_id": remote_message_id,
                        "raw_email": raw_email,
                        "remote_folder": runtime.mailbox_folder,
                    },
                )
                queued += 1

        async with db_manager.session() as session:
            await self.mail_account_service.update_graph_delta_link(session, runtime.id, delta_result.delta_link)
            if delta_result.messages:
                synthetic_counter = (runtime.last_seen_uid or 0) + len(delta_result.messages)
                await self.mail_account_service.mark_seen(session, runtime.id, synthetic_counter)

        return MailboxSyncState(
            queued=queued,
            synced=synced,
            highest_uid=None,
            active=True,
            poll_seconds=runtime.listen_interval_seconds,
        )

    async def analyze_raw_email(
        self,
        *,
        mail_account_id: str,
        uid: int | None,
        remote_message_id: str | None = None,
        raw_email: str,
        remote_folder: str,
    ) -> dict[str, str | int]:
        async with db_manager.session() as session:
            account = await self.mail_account_service.get_account(session, mail_account_id)
            existing = None
            if remote_message_id:
                existing = await self.email_service.get_by_remote_message_id(
                    session,
                    mailbox_account_id=mail_account_id,
                    remote_message_id=remote_message_id,
                )
            elif uid is not None:
                existing = await self.email_service.get_by_mailbox_uid(
                    session,
                    mailbox_account_id=mail_account_id,
                    remote_folder=remote_folder,
                    remote_uid=uid,
                )
            if existing is not None:
                await self.mail_account_service.mark_synced(session, mail_account_id, uid or ((account.last_synced_uid or 0) + 1))
                return {"status": "duplicate", "email_id": existing.id, "uid": uid or 0}

            parsed = self.email_service.parser.parse_raw_email(raw_email)
            result = await self.email_service.ingest_and_analyze(
                session,
                parsed_email=parsed,
                source=EmailSource.API,
                actor=account.owner_email,
                event_type=AuditEventType.EMAIL_ANALYZED,
                mailbox_account_id=mail_account_id,
                remote_uid=uid,
                remote_message_id=remote_message_id,
                remote_folder=remote_folder,
            )
            await self.mail_account_service.mark_synced(session, mail_account_id, uid or ((account.last_synced_uid or 0) + 1))
            return {"status": getattr(result, "status", "analyzed"), "email_id": result.email_id, "uid": uid or 0}
