from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.enums import MailboxProvider, MailboxStatus
from app.models.mail_account import MailAccount
from app.schemas.mail_account import MailAccountCreate, MailAccountUpdate
from app.services.mail_account_service import MailAccountService


def make_account() -> MailAccount:
    return MailAccount(
        owner_email="owner@example.com",
        email_address="user@example.com",
        display_name="Primary mailbox",
        provider=MailboxProvider.QQ,
        auth_type="password",
        sync_mode="imap",
        listener_mode="polling",
        imap_host="imap.qq.com",
        imap_port=993,
        imap_username="user@example.com",
        imap_password="encrypted-secret",
        mailbox_folder="INBOX",
        use_ssl=True,
        is_active=True,
        status=MailboxStatus.IDLE,
        listen_interval_seconds=5,
        connect_timeout_seconds=20,
    )


@pytest.mark.asyncio
async def test_create_account_refreshes_instance_after_initialization() -> None:
    service = MailAccountService()
    service._ensure_email_not_exists = AsyncMock()
    service.initialize_cursor_from_current_mailbox = AsyncMock()

    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    payload = MailAccountCreate(
        owner_email="owner@example.com",
        email_address="user@example.com",
        provider=MailboxProvider.QQ,
        imap_password="secret",
    )

    await service.create_account(session, payload)

    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_account_refreshes_instance_after_flush() -> None:
    service = MailAccountService()
    service._ensure_email_not_exists = AsyncMock()
    service.initialize_cursor_from_current_mailbox = AsyncMock()

    session = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()

    account = make_account()
    payload = MailAccountUpdate(display_name="Updated mailbox")

    updated = await service.update_account(session, account, payload)

    assert updated.display_name == "Updated mailbox"
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once_with(account)
    service.initialize_cursor_from_current_mailbox.assert_not_awaited()
