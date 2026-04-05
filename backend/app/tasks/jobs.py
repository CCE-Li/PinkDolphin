import asyncio

from app.core.config import get_settings
from app.services.auto_ingest_service import AutoIngestService
from app.services.mailbox_sync_service import MailboxSyncService
from app.tasks.celery_app import celery_app

settings = get_settings()


@celery_app.task(name="emails.reanalyze")
def reanalyze_email_task(email_id: str) -> dict[str, str]:
    return {"status": "queued", "email_id": email_id, "task": "reanalyze"}


@celery_app.task(name="iocs.backtrace")
def bulk_ioc_backtrace_task(indicator: str) -> dict[str, str]:
    return {"status": "queued", "indicator": indicator, "task": "ioc_backtrace"}


@celery_app.task(name="emails.poll_inbox")
def poll_inbox_task() -> dict[str, int]:
    service = AutoIngestService()
    return asyncio.run(service.process_inbox_once())


@celery_app.task(name="mailboxes.sync_account")
def sync_mail_account_task(account_id: str) -> dict[str, int | str | None]:
    service = MailboxSyncService()
    state = asyncio.run(service.sync_account_once(account_id))
    return {
        "account_id": account_id,
        "queued": state.queued,
        "synced": state.synced,
        "highest_uid": state.highest_uid,
    }


@celery_app.task(
    name="mailboxes.analyze_raw_email",
    queue=settings.mailbox_analysis_queue,
    rate_limit=settings.mailbox_analysis_rate_limit,
)
def analyze_mailbox_email_task(
    mail_account_id: str,
    uid: int,
    raw_email: str,
    remote_folder: str,
    remote_message_id: str | None = None,
) -> dict[str, str | int]:
    service = MailboxSyncService()
    return asyncio.run(
        service.analyze_raw_email(
            mail_account_id=mail_account_id,
            uid=uid,
            remote_message_id=remote_message_id,
            raw_email=raw_email,
            remote_folder=remote_folder,
        )
    )
