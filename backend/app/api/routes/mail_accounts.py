from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.security import require_admin_token
from app.schemas.mail_account import (
    MailAccountCreate,
    MailAccountRead,
    MailAccountSyncResult,
    MailAccountTestResult,
    MailAccountUpdate,
    MailProviderPresetRead,
    OutlookOAuthStartRequest,
    OutlookOAuthStartResponse,
)
from app.services.mail_account_service import MailAccountService
from app.services.mailbox_sync_service import MailboxSyncService

router = APIRouter()
mail_account_service = MailAccountService()
mailbox_sync_service = MailboxSyncService()


@router.get("", response_model=list[MailAccountRead], dependencies=[Depends(require_admin_token)])
async def list_mail_accounts(session: AsyncSession = Depends(get_db_session)) -> list[MailAccountRead]:
    accounts = await mail_account_service.list_accounts(session)
    hydrated = [await mail_account_service.hydrate_account_progress(session, account) for account in accounts]
    return [await mail_account_service.to_read_model(session, account) for account in hydrated]


@router.get("/providers", response_model=list[MailProviderPresetRead], dependencies=[Depends(require_admin_token)])
async def list_mail_providers() -> list[MailProviderPresetRead]:
    return mail_account_service.list_provider_presets()


@router.post("/oauth/outlook/start", response_model=OutlookOAuthStartResponse, dependencies=[Depends(require_admin_token)])
async def start_outlook_oauth(payload: OutlookOAuthStartRequest) -> OutlookOAuthStartResponse:
    return OutlookOAuthStartResponse(authorization_url=await mail_account_service.start_outlook_oauth(payload))


@router.get("/oauth/outlook/callback", include_in_schema=False, dependencies=[])
async def complete_outlook_oauth(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    if error:
        return RedirectResponse(
            url=mail_account_service.build_outlook_callback_redirect(success=False, message=error),
            status_code=302,
        )
    if not code or not state:
        return RedirectResponse(
            url=mail_account_service.build_outlook_callback_redirect(success=False, message="Missing OAuth callback code or state"),
            status_code=302,
        )
    try:
        account = await mail_account_service.complete_outlook_oauth(session, code=code, state=state)
        return RedirectResponse(
            url=mail_account_service.build_outlook_callback_redirect(
                success=True,
                message=f"{account.email_address} connected",
                account_id=account.id,
            ),
            status_code=302,
        )
    except Exception as exc:
        return RedirectResponse(
            url=mail_account_service.build_outlook_callback_redirect(success=False, message=str(exc)),
            status_code=302,
        )


@router.post("", response_model=MailAccountRead, dependencies=[Depends(require_admin_token)])
async def create_mail_account(
    payload: MailAccountCreate,
    session: AsyncSession = Depends(get_db_session),
) -> MailAccountRead:
    account = await mail_account_service.create_account(session, payload)
    await mail_account_service.hydrate_account_progress(session, account)
    return await mail_account_service.to_read_model(session, account)


@router.put("/{account_id}", response_model=MailAccountRead, dependencies=[Depends(require_admin_token)])
async def update_mail_account(
    account_id: str,
    payload: MailAccountUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> MailAccountRead:
    account = await mail_account_service.get_account(session, account_id)
    updated = await mail_account_service.update_account(session, account, payload)
    await mail_account_service.hydrate_account_progress(session, updated)
    return await mail_account_service.to_read_model(session, updated)


@router.delete("/{account_id}", dependencies=[Depends(require_admin_token)])
async def delete_mail_account(
    account_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, int | str]:
    account = await mail_account_service.get_account(session, account_id)
    deleted_email_count = await mail_account_service.delete_account(session, account)
    return {"account_id": account_id, "deleted_email_count": deleted_email_count, "status": "deleted"}


@router.post("/{account_id}/test", response_model=MailAccountTestResult, dependencies=[Depends(require_admin_token)])
async def test_mail_account(
    account_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> MailAccountTestResult:
    account = await mail_account_service.get_account(session, account_id)
    await mail_account_service.hydrate_account_progress(session, account)
    return await mail_account_service.test_connection(session, account)


@router.post("/{account_id}/sync", response_model=MailAccountSyncResult, dependencies=[Depends(require_admin_token)])
async def sync_mail_account(
    account_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> MailAccountSyncResult:
    await mail_account_service.get_account(session, account_id)
    state = await mailbox_sync_service.sync_account_once(account_id)
    return MailAccountSyncResult(account_id=account_id, queued=state.queued, synced=state.synced, highest_uid=state.highest_uid)
