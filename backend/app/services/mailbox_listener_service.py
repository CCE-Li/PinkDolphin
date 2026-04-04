from __future__ import annotations

import asyncio
import contextlib
import logging

from sqlalchemy.exc import ProgrammingError

from app.core.config import get_settings
from app.db.session import db_manager
from app.services.mail_account_service import MailAccountService
from app.services.mailbox_sync_service import MailboxSyncService

logger = logging.getLogger(__name__)


class MailboxListenerService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.mail_account_service = MailAccountService()
        self.mailbox_sync_service = MailboxSyncService()
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._missing_table_logged = False

    async def run_loop(self, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            await self._refresh_account_tasks(stop_event)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self.settings.mailbox_listener_refresh_seconds)
            except TimeoutError:
                continue

        for task in self._tasks.values():
            task.cancel()
        for task in list(self._tasks.values()):
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

    async def _refresh_account_tasks(self, stop_event: asyncio.Event) -> None:
        try:
            async with db_manager.session() as session:
                accounts = await self.mail_account_service.list_active_accounts(session)
        except ProgrammingError as exc:
            if self._is_missing_mail_accounts_table(exc):
                if not self._missing_table_logged:
                    logger.warning(
                        "mailbox_listener_skipped_missing_table",
                        extra={"table": "mail_accounts", "hint": "run alembic upgrade head"},
                    )
                    self._missing_table_logged = True
                return
            raise

        self._missing_table_logged = False

        active_ids = {account.id for account in accounts}
        for account_id in list(self._tasks):
            if account_id not in active_ids:
                self._tasks[account_id].cancel()
                del self._tasks[account_id]

        for account in accounts:
            if account.id not in self._tasks or self._tasks[account.id].done():
                self._tasks[account.id] = asyncio.create_task(self._listen_account(account.id, stop_event))

    def _is_missing_mail_accounts_table(self, exc: ProgrammingError) -> bool:
        return 'relation "mail_accounts" does not exist' in str(exc).lower()

    async def _listen_account(self, account_id: str, stop_event: asyncio.Event) -> None:
        while not stop_event.is_set():
            client = None
            try:
                async with db_manager.session() as session:
                    account = await self.mail_account_service.get_account(session, account_id)
                    runtime = self.mail_account_service.to_runtime(account)
                    await self.mail_account_service.mark_listening(session, account_id)

                client = await asyncio.to_thread(self.mail_account_service.imap_client.connect, runtime)
                while not stop_event.is_set():
                    state = await self.mailbox_sync_service.sync_account_once(account_id, client=client)
                    if not state.active:
                        return
                    try:
                        await asyncio.wait_for(stop_event.wait(), timeout=state.poll_seconds)
                    except TimeoutError:
                        await asyncio.to_thread(self.mail_account_service.imap_client.noop, client)
                        continue
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                async with db_manager.session() as session:
                    await self.mail_account_service.mark_error(session, account_id, str(exc))
                try:
                    await asyncio.wait_for(stop_event.wait(), timeout=self.settings.mailbox_listener_retry_seconds)
                except TimeoutError:
                    pass
            finally:
                if client is not None:
                    with contextlib.suppress(Exception):
                        await asyncio.to_thread(self.mail_account_service.imap_client.close, client)
