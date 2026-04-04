import asyncio
from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException, DeferredAnalysisError
from app.models.analysis import AnalysisResult
from app.models.attachment import Attachment
from app.models.contact_history import ContactHistory
from app.models.email import Email
from app.models.email_address import EmailAddress
from app.models.incident import Incident
from app.models.enums import AddressRole, AuditEventType, EmailSource, EmailStatus, IssueSeverity
from app.models.action import Action
from app.models.url import Url
from app.schemas.analysis import AnalysisResultRead, AnalyzerResultRead
from app.schemas.email import (
    EmailAnalyzeDeferredResponse,
    EmailAnalyzeRequest,
    EmailAnalyzeResponse,
    EmailDetail,
    EmailListItem,
    ParsedEmailSchema,
)
from app.services.analysis_engine import AnalysisEngine
from app.services.issue_log_service import IssueLogService
from app.services.mail_account_service import MailAccountService
from app.services.parser import EmailParserService, url_to_domain_path


class EmailService:
    def __init__(self) -> None:
        self.parser = EmailParserService()
        self.analysis_engine = AnalysisEngine()
        self.mail_account_service = MailAccountService()
        self.issue_log_service = IssueLogService()

    async def list_emails(self, session: AsyncSession) -> list[Email]:
        result = await session.execute(
            select(Email)
            .options(selectinload(Email.analysis_results), selectinload(Email.mail_account))
            .order_by(Email.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_email(self, session: AsyncSession, email_id: str) -> Email:
        stmt = (
            select(Email)
            .where(Email.id == email_id)
            .options(
                selectinload(Email.addresses),
                selectinload(Email.attachments),
                selectinload(Email.urls),
                selectinload(Email.analysis_results).selectinload(AnalysisResult.analyzer_results),
                selectinload(Email.mail_account),
            )
        )
        email = (await session.execute(stmt)).scalar_one_or_none()
        if email is None:
            raise AppException(status_code=404, code="email_not_found", message="Email not found")
        return email

    async def get_by_mailbox_uid(
        self,
        session: AsyncSession,
        *,
        mailbox_account_id: str,
        remote_folder: str,
        remote_uid: int,
    ) -> Email | None:
        stmt = select(Email).where(
            Email.mailbox_account_id == mailbox_account_id,
            Email.remote_folder == remote_folder,
            Email.remote_uid == remote_uid,
        )
        return (await session.execute(stmt)).scalar_one_or_none()

    async def delete_email(self, session: AsyncSession, email: Email) -> None:
        deleted_from_mailbox = False
        mailbox_delete_skipped_reason: str | None = None
        if email.mailbox_account_id and email.remote_uid and email.mail_account is not None:
            try:
                runtime = self.mail_account_service.to_runtime(email.mail_account)
                client = await asyncio.to_thread(self.mail_account_service.imap_client.connect, runtime, readonly=False)
                try:
                    mailbox_folder = email.remote_folder or runtime.mailbox_folder
                    await asyncio.to_thread(
                        self.mail_account_service.imap_client.select_mailbox,
                        client,
                        mailbox_folder,
                        readonly=False,
                    )
                    await asyncio.to_thread(self.mail_account_service.imap_client.delete_message, client, email.remote_uid)
                finally:
                    await asyncio.to_thread(self.mail_account_service.imap_client.close, client)
                deleted_from_mailbox = True
            except Exception as exc:
                await self.issue_log_service.log_detached(
                    component="email:delete",
                    severity=IssueSeverity.ERROR,
                    message="Failed to delete email from mailbox via IMAP",
                    details={
                        "email_id": email.id,
                        "mailbox_account_id": email.mailbox_account_id,
                        "mailbox_email_address": email.mail_account.email_address,
                        "remote_uid": email.remote_uid,
                        "remote_folder": email.remote_folder,
                        "error": str(exc),
                    },
                )
                raise AppException(
                    status_code=502,
                    code="imap_delete_failed",
                    message="Failed to delete email from mailbox via IMAP",
                ) from exc
        elif email.mailbox_account_id:
            if email.mail_account is None:
                mailbox_delete_skipped_reason = "mail_account_not_loaded_or_missing"
            elif email.remote_uid is None:
                mailbox_delete_skipped_reason = "remote_uid_missing"

        histories = list(
            (
                await session.execute(
                    select(ContactHistory).where(ContactHistory.last_email_id == email.id)
                )
            ).scalars().all()
        )
        for history in histories:
            history.last_email_id = None

        await session.execute(delete(Incident).where(Incident.email_id == email.id))
        await session.execute(delete(Action).where(Action.email_id == email.id))

        # Break the self-reference before cascading delete analysis_results.
        email.latest_analysis_id = None
        email.latest_risk_level = None
        email.latest_score = None
        await session.flush()
        await session.delete(email)
        await session.flush()
        await self.issue_log_service.log(
            session,
            component="email:delete",
            severity=IssueSeverity.INFO,
            message="Email deleted",
            details={
                "email_id": email.id,
                "message_id": email.message_id,
                "subject": email.subject,
                "mailbox_account_id": email.mailbox_account_id,
                "mailbox_email_address": email.mail_account.email_address if email.mail_account else None,
                "remote_uid": email.remote_uid,
                "deleted_from_mailbox": deleted_from_mailbox,
                "mailbox_delete_skipped_reason": mailbox_delete_skipped_reason,
            },
        )

    def parse_request(self, payload: EmailAnalyzeRequest) -> ParsedEmailSchema:
        if payload.raw_email:
            return self.parser.parse_raw_email(payload.raw_email)
        if payload.structured_email:
            return self.parser.parse_structured_email(payload.structured_email)
        raise AppException(status_code=400, code="invalid_request", message="raw_email or structured_email required")

    async def ingest_and_analyze(
        self,
        session: AsyncSession,
        *,
        parsed_email: ParsedEmailSchema,
        source: EmailSource,
        actor: str,
        event_type: AuditEventType,
        mailbox_account_id: str | None = None,
        remote_uid: int | None = None,
        remote_folder: str | None = None,
    ) -> EmailAnalyzeResponse | EmailAnalyzeDeferredResponse:
        email = Email(
            message_id=parsed_email.message_id,
            subject=parsed_email.subject,
            authentication_results=parsed_email.authentication_results,
            send_time=parsed_email.send_time,
            raw_headers=parsed_email.raw_headers,
            body_text=parsed_email.body_text,
            body_html=parsed_email.body_html,
            source=source,
            raw_email=parsed_email.raw_email,
            mailbox_account_id=mailbox_account_id,
            remote_uid=remote_uid,
            remote_folder=remote_folder,
        )
        session.add(email)
        await session.flush()
        await self._persist_addresses(session, email, parsed_email)
        await self._persist_urls(session, email, parsed_email)
        await self._persist_attachments(session, email, parsed_email)
        await self._update_contact_history(session, email, parsed_email)
        try:
            return await self.analysis_engine.analyze_email(
                session,
                email=email,
                parsed_email=parsed_email,
                actor=actor,
                event_type=event_type,
            )
        except DeferredAnalysisError as exc:
            email.status = EmailStatus.RECEIVED
            email.latest_analysis_id = None
            email.latest_risk_level = None
            email.latest_score = None
            await self.issue_log_service.log(
                session,
                component="analysis:deferred",
                severity=IssueSeverity.WARNING,
                message="Email moved back to pending because analysis could not complete",
                details={
                    "email_id": email.id,
                    "subject": email.subject,
                    "component": exc.component,
                    "reason": exc.message,
                    "mailbox_account_id": email.mailbox_account_id,
                },
            )
            return EmailAnalyzeDeferredResponse(
                email_id=email.id,
                status=EmailStatus.RECEIVED.value,
                message="LLM processing failed, email returned to pending",
                component=exc.component,
            )

    async def reanalyze(
        self,
        session: AsyncSession,
        *,
        email: Email,
        actor: str,
    ) -> EmailAnalyzeResponse | EmailAnalyzeDeferredResponse:
        parsed_email = ParsedEmailSchema(
            message_id=email.message_id,
            subject=email.subject,
            authentication_results=email.authentication_results,
            send_time=email.send_time,
            raw_headers=email.raw_headers,
            body_text=email.body_text,
            body_html=email.body_html,
            raw_email=email.raw_email,
            from_name=next((item.display_name for item in email.addresses if item.role == AddressRole.FROM), None),
            from_email=next((item.address for item in email.addresses if item.role == AddressRole.FROM), None),
            reply_to=next((item.address for item in email.addresses if item.role == AddressRole.REPLY_TO), None),
            return_path=next((item.address for item in email.addresses if item.role == AddressRole.RETURN_PATH), None),
            to_recipients=[
                {"name": item.display_name, "email": item.address} for item in email.addresses if item.role == AddressRole.TO
            ],
            cc_recipients=[
                {"name": item.display_name, "email": item.address} for item in email.addresses if item.role == AddressRole.CC
            ],
            links=[item.url for item in email.urls],
            attachments=[
                {
                    "filename": item.filename,
                    "content_type": item.content_type,
                    "size": item.size,
                    "sha256": item.sha256,
                    "content_base64": item.metadata_json.get("content_base64") if isinstance(item.metadata_json, dict) else None,
                }
                for item in email.attachments
            ],
        )
        try:
            return await self.analysis_engine.analyze_email(
                session,
                email=email,
                parsed_email=parsed_email,
                actor=actor,
                event_type=AuditEventType.EMAIL_REANALYZED,
            )
        except DeferredAnalysisError as exc:
            email.status = EmailStatus.RECEIVED
            email.latest_analysis_id = None
            email.latest_risk_level = None
            email.latest_score = None
            await self.issue_log_service.log(
                session,
                component="analysis:deferred",
                severity=IssueSeverity.WARNING,
                message="Email reanalysis deferred and returned to pending",
                details={
                    "email_id": email.id,
                    "subject": email.subject,
                    "component": exc.component,
                    "reason": exc.message,
                },
            )
            return EmailAnalyzeDeferredResponse(
                email_id=email.id,
                status=EmailStatus.RECEIVED.value,
                message="LLM processing failed, email returned to pending",
                component=exc.component,
            )

    async def _persist_addresses(self, session: AsyncSession, email: Email, parsed_email: ParsedEmailSchema) -> None:
        items: list[EmailAddress] = []
        if parsed_email.from_email:
            items.append(
                EmailAddress(
                    email_id=email.id,
                    display_name=parsed_email.from_name,
                    address=parsed_email.from_email.lower(),
                    role=AddressRole.FROM,
                )
            )
        if parsed_email.reply_to:
            items.append(EmailAddress(email_id=email.id, address=parsed_email.reply_to.lower(), role=AddressRole.REPLY_TO))
        if parsed_email.return_path:
            items.append(
                EmailAddress(email_id=email.id, address=parsed_email.return_path.lower(), role=AddressRole.RETURN_PATH)
            )
        for recipient in parsed_email.to_recipients:
            items.append(
                EmailAddress(
                    email_id=email.id,
                    display_name=recipient.name,
                    address=recipient.email.lower(),
                    role=AddressRole.TO,
                )
            )
        for recipient in parsed_email.cc_recipients:
            items.append(
                EmailAddress(
                    email_id=email.id,
                    display_name=recipient.name,
                    address=recipient.email.lower(),
                    role=AddressRole.CC,
                )
            )
        session.add_all(items)
        await session.flush()

    async def _persist_urls(self, session: AsyncSession, email: Email, parsed_email: ParsedEmailSchema) -> None:
        items = []
        for index, link in enumerate(parsed_email.links):
            domain, path = url_to_domain_path(link)
            items.append(
                Url(
                    email_id=email.id,
                    url=link,
                    domain=domain,
                    path=path,
                    is_shortened=bool(domain and domain in {"bit.ly", "t.co", "tinyurl.com"}),
                    position=index,
                )
            )
        session.add_all(items)
        await session.flush()

    async def _persist_attachments(self, session: AsyncSession, email: Email, parsed_email: ParsedEmailSchema) -> None:
        items = [
            Attachment(
                email_id=email.id,
                filename=attachment.get("filename"),
                content_type=attachment.get("content_type"),
                size=int(attachment.get("size") or 0),
                sha256=attachment.get("sha256"),
                metadata_json={"content_base64": attachment.get("content_base64")},
            )
            for attachment in parsed_email.attachments
        ]
        session.add_all(items)
        await session.flush()

    async def _update_contact_history(self, session: AsyncSession, email: Email, parsed_email: ParsedEmailSchema) -> None:
        sender = (parsed_email.from_email or "").lower()
        timestamp = parsed_email.send_time or datetime.now(timezone.utc)
        for recipient in parsed_email.to_recipients:
            recipient_email = recipient.email.lower()
            stmt = select(ContactHistory).where(
                ContactHistory.sender_email == sender,
                ContactHistory.recipient_email == recipient_email,
            )
            history = (await session.execute(stmt)).scalar_one_or_none()
            if history is None:
                session.add(
                    ContactHistory(
                        sender_email=sender,
                        recipient_email=recipient_email,
                        first_seen_at=timestamp,
                        last_seen_at=timestamp,
                        seen_count=1,
                        last_email_id=email.id,
                    )
                )
            else:
                history.last_seen_at = timestamp
                history.last_email_id = email.id
                history.seen_count += 1
        await session.flush()

    @staticmethod
    def to_list_item(email: Email) -> EmailListItem:
        latest_analysis = None
        if email.analysis_results:
            latest_analysis = sorted(email.analysis_results, key=lambda item: item.created_at)[-1]
        return EmailListItem(
            id=email.id,
            created_at=email.created_at,
            updated_at=email.updated_at,
            message_id=email.message_id,
            subject=email.subject,
            source=email.source,
            status=email.status,
            mailbox_account_id=email.mailbox_account_id,
            mailbox_display_name=email.mail_account.display_name if email.mail_account else None,
            mailbox_email_address=email.mail_account.email_address if email.mail_account else None,
            remote_uid=email.remote_uid,
            latest_risk_level=email.latest_risk_level,
            latest_score=email.latest_score,
            latest_recommended_action=latest_analysis.recommended_action.value if latest_analysis else None,
        )

    @staticmethod
    def to_detail(email: Email) -> EmailDetail:
        return EmailDetail(
            id=email.id,
            created_at=email.created_at,
            updated_at=email.updated_at,
            message_id=email.message_id,
            subject=email.subject,
            authentication_results=email.authentication_results,
            send_time=email.send_time,
            raw_headers=email.raw_headers,
            raw_email=email.raw_email,
            body_text=email.body_text,
            body_html=email.body_html,
            source=email.source,
            status=email.status,
            mailbox_account_id=email.mailbox_account_id,
            remote_uid=email.remote_uid,
            remote_folder=email.remote_folder,
            latest_risk_level=email.latest_risk_level,
            latest_score=email.latest_score,
            addresses=[
                {"id": item.id, "display_name": item.display_name, "address": item.address, "role": item.role.value}
                for item in email.addresses
            ],
            attachments=[
                {
                    "id": item.id,
                    "filename": item.filename,
                    "content_type": item.content_type,
                    "size": item.size,
                    "sha256": item.sha256,
                }
                for item in email.attachments
            ],
            urls=[
                {
                    "id": item.id,
                    "url": item.url,
                    "domain": item.domain,
                    "path": item.path,
                    "is_shortened": item.is_shortened,
                }
                for item in email.urls
            ],
            analysis_results=[
                AnalysisResultRead(
                    id=analysis.id,
                    created_at=analysis.created_at,
                    updated_at=analysis.updated_at,
                    email_id=analysis.email_id,
                    total_score=analysis.total_score,
                    risk_level=analysis.risk_level,
                    recommended_action=analysis.recommended_action,
                    summary=analysis.summary,
                    override_reason=analysis.override_reason,
                    decision_details=analysis.decision_details,
                    analyzer_results=[
                        AnalyzerResultRead(
                            id=result.id,
                            created_at=result.created_at,
                            updated_at=result.updated_at,
                            analysis_result_id=result.analysis_result_id,
                            analyzer_name=result.analyzer_name,
                            enabled=result.enabled,
                            status=result.status,
                            score=result.score,
                            severity=result.severity,
                            summary=result.summary,
                            signals=result.signals,
                            evidence=result.evidence,
                        )
                        for result in analysis.analyzer_results
                    ],
                )
                for analysis in email.analysis_results
            ],
        )
