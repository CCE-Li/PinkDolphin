import asyncio
import logging
from pathlib import Path
from shutil import move

from app.core.config import get_settings
from app.db.session import db_manager
from app.models.enums import AuditEventType, EmailSource
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class AutoIngestService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.email_service = EmailService()

    def ensure_directories(self) -> None:
        self.settings.inbox_path.mkdir(parents=True, exist_ok=True)
        self.settings.processed_path.mkdir(parents=True, exist_ok=True)
        self.settings.failed_path.mkdir(parents=True, exist_ok=True)

    def list_pending_files(self) -> list[Path]:
        self.ensure_directories()
        return sorted(
            [path for path in self.settings.inbox_path.glob("*.eml") if path.is_file()],
            key=lambda item: item.stat().st_mtime,
        )

    async def process_inbox_once(self) -> dict[str, int]:
        self.ensure_directories()
        files = self.list_pending_files()
        processed = 0
        failed = 0

        for path in files:
            try:
                raw_email = path.read_text(encoding="utf-8", errors="replace")
                parsed = self.email_service.parser.parse_raw_email(raw_email)
                async with db_manager.session() as session:
                    await self.email_service.ingest_and_analyze(
                        session,
                        parsed_email=parsed,
                        source=EmailSource.UPLOAD,
                        actor="auto-ingest",
                        event_type=AuditEventType.EMAIL_ANALYZED,
                    )
                move(str(path), str(self.settings.processed_path / path.name))
                processed += 1
                logger.info("auto_ingest_processed", extra={"filename": path.name})
            except Exception as exc:
                failed += 1
                logger.exception("auto_ingest_failed", extra={"filename": path.name, "error": str(exc)})
                move(str(path), str(self.settings.failed_path / path.name))

        return {"processed": processed, "failed": failed, "pending": len(self.list_pending_files())}

    async def run_loop(self, stop_event: asyncio.Event) -> None:
        self.ensure_directories()
        while not stop_event.is_set():
            await self.process_inbox_once()
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=self.settings.auto_ingest_poll_seconds)
            except TimeoutError:
                continue
