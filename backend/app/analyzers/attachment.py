from app.analyzers.base import BaseAnalyzer
from app.integrations.antivirus import AntivirusGateway
from app.models.enums import AnalyzerExecutionStatus, IssueSeverity, SeverityLevel
from app.schemas.analysis import AnalyzerOutput
from app.services.context import EmailAnalysisContext
from app.services.issue_log_service import IssueLogService


class AttachmentAnalyzer(BaseAnalyzer):
    name = "attachment"

    def __init__(self) -> None:
        self.antivirus = AntivirusGateway()
        self.issue_log_service = IssueLogService()

    async def analyze(self, email_context: EmailAnalysisContext) -> AnalyzerOutput:
        if not email_context.allow_attachment:
            return AnalyzerOutput(
                analyzer_name=self.name,
                enabled=False,
                status=AnalyzerExecutionStatus.SKIPPED,
                score=0,
                severity=SeverityLevel.INFO,
                summary="Attachment analysis skipped due to privacy allowlist policy",
                signals=["privacy_allowlist_skip"],
                evidence={"allowlist_hits": email_context.privacy_allowlist_hits},
            )

        score = 0
        hits: list[str] = []
        scanned: list[dict[str, object]] = []
        try:
            for attachment in email_context.parsed_email.attachments:
                await self.issue_log_service.log_detached(
                    component="analyzer:attachment",
                    severity=IssueSeverity.INFO,
                    message="Attachment malware lookup started",
                    details={
                        "email_id": email_context.email_id,
                        "filename": attachment.get("filename"),
                        "sha256": attachment.get("sha256"),
                    },
                )
                result = await self.antivirus.scan_attachment(
                    filename=attachment.get("filename"),
                    content_type=attachment.get("content_type"),
                    size=int(attachment.get("size") or 0),
                    sha256=attachment.get("sha256"),
                    content_base64=attachment.get("content_base64"),
                )
                await self.issue_log_service.log_detached(
                    component="analyzer:attachment",
                    severity=IssueSeverity.INFO,
                    message="Attachment malware lookup completed",
                    details={
                        "email_id": email_context.email_id,
                        "filename": attachment.get("filename"),
                        "sha256": attachment.get("sha256"),
                        "provider": result.get("provider"),
                        "score": result.get("score"),
                        "hits": list(result.get("hits", [])),
                    },
                )
                score += int(result["score"])
                hits.extend(result["hits"])  # type: ignore[arg-type]
                scanned.append({**attachment, **result})
        except Exception as exc:
            await self.issue_log_service.log_detached(
                component="analyzer:attachment",
                severity=IssueSeverity.ERROR,
                message="Attachment malware lookup failed",
                details={"email_id": email_context.email_id, "error": str(exc), "attachments": scanned},
            )
            return AnalyzerOutput(
                analyzer_name=self.name,
                enabled=True,
                status=AnalyzerExecutionStatus.ERROR,
                score=0,
                severity=SeverityLevel.INFO,
                summary="Attachment analysis provider failed",
                signals=["attachment_provider_error"],
                evidence={"error": str(exc), "attachments": scanned},
            )

        severity = SeverityLevel.INFO
        if score >= 60:
            severity = SeverityLevel.HIGH
        elif score >= 20:
            severity = SeverityLevel.MEDIUM
        elif score > 0:
            severity = SeverityLevel.LOW

        return AnalyzerOutput(
            analyzer_name=self.name,
            score=score,
            severity=severity,
            summary="Attachments scanned by malware analysis provider",
            signals=hits,
            evidence={"attachments": scanned},
        )
