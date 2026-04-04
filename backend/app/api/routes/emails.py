from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db_session
from app.core.exceptions import AppException
from app.core.security import require_admin_token
from app.models.enums import AuditEventType, EmailSource
from app.schemas.email import (
    EmailActionRequest,
    EmailAnalyzeDeferredResponse,
    EmailAnalyzeRequest,
    EmailAnalyzeResponse,
    EmailDetail,
    EmailListItem,
)
from app.services.action_service import ActionService
from app.services.auto_ingest_service import AutoIngestService
from app.services.email_service import EmailService
from app.core.config import get_settings

router = APIRouter(dependencies=[Depends(require_admin_token)])

email_service = EmailService()
action_service = ActionService()
auto_ingest_service = AutoIngestService()


@router.post("/upload", response_model=EmailAnalyzeResponse | EmailAnalyzeDeferredResponse)
async def upload_email(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> EmailAnalyzeResponse | EmailAnalyzeDeferredResponse:
    settings = get_settings()
    if not file.filename or not file.filename.endswith(".eml"):
        raise AppException(status_code=400, code="invalid_file", message="Only .eml files are supported")
    payload = await file.read()
    if len(payload) > settings.max_upload_size_mb * 1024 * 1024:
        raise AppException(status_code=413, code="file_too_large", message="Uploaded file exceeds limit")
    parsed = email_service.parser.parse_raw_email(payload.decode("utf-8", errors="replace"))
    return await email_service.ingest_and_analyze(
        session,
        parsed_email=parsed,
        source=EmailSource.UPLOAD,
        actor="admin",
        event_type=AuditEventType.EMAIL_ANALYZED,
    )


@router.post("/analyze", response_model=EmailAnalyzeResponse | EmailAnalyzeDeferredResponse)
async def analyze_email(
    payload: EmailAnalyzeRequest,
    session: AsyncSession = Depends(get_db_session),
) -> EmailAnalyzeResponse | EmailAnalyzeDeferredResponse:
    parsed = email_service.parse_request(payload)
    return await email_service.ingest_and_analyze(
        session,
        parsed_email=parsed,
        source=payload.source,
        actor="admin",
        event_type=AuditEventType.EMAIL_ANALYZED,
    )


@router.get("", response_model=list[EmailListItem])
async def list_emails(session: AsyncSession = Depends(get_db_session)) -> list[EmailListItem]:
    emails = await email_service.list_emails(session)
    return [email_service.to_list_item(email) for email in emails]


@router.get("/{email_id}", response_model=EmailDetail)
async def get_email(email_id: str, session: AsyncSession = Depends(get_db_session)) -> EmailDetail:
    email = await email_service.get_email(session, email_id)
    return email_service.to_detail(email)


@router.delete("/{email_id}")
async def delete_email(email_id: str, session: AsyncSession = Depends(get_db_session)) -> dict[str, str]:
    email = await email_service.get_email(session, email_id)
    await email_service.delete_email(session, email)
    return {"email_id": email_id, "status": "deleted"}


@router.post("/{email_id}/reanalyze", response_model=EmailAnalyzeResponse | EmailAnalyzeDeferredResponse)
async def reanalyze_email(
    email_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> EmailAnalyzeResponse | EmailAnalyzeDeferredResponse:
    email = await email_service.get_email(session, email_id)
    return await email_service.reanalyze(session, email=email, actor="admin")


@router.post("/{email_id}/action")
async def apply_action(
    email_id: str,
    payload: EmailActionRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    email = await email_service.get_email(session, email_id)
    action = await action_service.create_action(session, email=email, payload=payload)
    return {"action_id": action.id, "status": "applied"}


@router.post("/auto-fetch/run")
async def run_auto_fetch() -> dict[str, int]:
    return await auto_ingest_service.process_inbox_once()


@router.get("/auto-fetch/status")
async def get_auto_fetch_status() -> dict[str, object]:
    settings = get_settings()
    pending_files = auto_ingest_service.list_pending_files()
    return {
        "enabled": settings.auto_ingest_enabled,
        "poll_seconds": settings.auto_ingest_poll_seconds,
        "inbox_dir": str(settings.inbox_path),
        "processed_dir": str(settings.processed_path),
        "failed_dir": str(settings.failed_path),
        "pending_count": len(pending_files),
        "pending_files": [item.name for item in pending_files],
    }
