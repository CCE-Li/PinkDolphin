from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import require_admin_token
from app.schemas.mail_account import (
    MailAccountCreate,
    MailAccountRead,
    MailAccountSyncResult,
    MailAccountTestResult,
    MailAccountUpdate,
)
from app.services.mail_account_service import MailAccountService
from app.services.mailbox_sync_service import MailboxSyncService

router = APIRouter(dependencies=[Depends(require_admin_token)])
mail_account_service = MailAccountService()
mailbox_sync_service = MailboxSyncService()


@router.get("", response_model=list[MailAccountRead])
async def list_mail_accounts(session: AsyncSession = Depends(get_db_session)) -> list[MailAccountRead]:
    accounts = await mail_account_service.list_accounts(session)
    hydrated = [await mail_account_service.hydrate_account_progress(session, account) for account in accounts]
    return [MailAccountRead.model_validate(account) for account in hydrated]


@router.post("", response_model=MailAccountRead)
async def create_mail_account(
    payload: MailAccountCreate,
    session: AsyncSession = Depends(get_db_session),
) -> MailAccountRead:
    account = await mail_account_service.create_account(session, payload)
    await mail_account_service.hydrate_account_progress(session, account)
    return MailAccountRead.model_validate(account)


@router.put("/{account_id}", response_model=MailAccountRead)
async def update_mail_account(
    account_id: str,
    payload: MailAccountUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> MailAccountRead:
    account = await mail_account_service.get_account(session, account_id)
    updated = await mail_account_service.update_account(session, account, payload)
    await mail_account_service.hydrate_account_progress(session, updated)
    return MailAccountRead.model_validate(updated)


@router.post("/{account_id}/test", response_model=MailAccountTestResult)
async def test_mail_account(
    account_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> MailAccountTestResult:
    account = await mail_account_service.get_account(session, account_id)
    await mail_account_service.hydrate_account_progress(session, account)
    return await mail_account_service.test_connection(session, account)


@router.post("/{account_id}/sync", response_model=MailAccountSyncResult)
async def sync_mail_account(
    account_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> MailAccountSyncResult:
    await mail_account_service.get_account(session, account_id)
    state = await mailbox_sync_service.sync_account_once(account_id, process_inline=True)
    return MailAccountSyncResult(account_id=account_id, queued=state.queued, synced=state.synced, highest_uid=state.highest_uid)
