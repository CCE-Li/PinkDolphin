from app.analyzers.base import BaseAnalyzer
from app.integrations.threat_intel import ThreatIntelGateway
from app.models.enums import AnalyzerExecutionStatus, IssueSeverity, SeverityLevel
from app.schemas.analysis import AnalyzerOutput
from app.services.context import EmailAnalysisContext
from app.services.issue_log_service import IssueLogService


class UrlAnalyzer(BaseAnalyzer):
    name = "url"

    def __init__(self) -> None:
        self.threat_intel = ThreatIntelGateway()
        self.issue_log_service = IssueLogService()

    async def analyze(self, email_context: EmailAnalysisContext) -> AnalyzerOutput:
        if not email_context.allow_url:
            return AnalyzerOutput(
                analyzer_name=self.name,
                enabled=False,
                status=AnalyzerExecutionStatus.SKIPPED,
                score=0,
                severity=SeverityLevel.INFO,
                summary="URL analysis skipped due to privacy allowlist policy",
                signals=["privacy_allowlist_skip"],
                evidence={"allowlist_hits": email_context.privacy_allowlist_hits},
            )

        score = 0
        hits: list[str] = []
        evidence: dict[str, object] = {"links": []}

        try:
            for url in email_context.parsed_email.links:
                await self.issue_log_service.log_detached(
                    component="analyzer:url",
                    severity=IssueSeverity.INFO,
                    message="URL threat lookup started",
                    details={"email_id": email_context.email_id, "url": url},
                )
                result = await self.threat_intel.lookup_url(url)
                await self.issue_log_service.log_detached(
                    component="analyzer:url",
                    severity=IssueSeverity.INFO,
                    message="URL threat lookup completed",
                    details={
                        "email_id": email_context.email_id,
                        "url": url,
                        "provider": result.get("provider"),
                        "score": result.get("score"),
                        "hits": list(result.get("hits", [])),
                    },
                )
                score += int(result["score"])
                hits.extend(result["hits"])  # type: ignore[arg-type]
                evidence["links"].append({"url": url, **result})  # type: ignore[union-attr]
        except Exception as exc:
            await self.issue_log_service.log_detached(
                component="analyzer:url",
                severity=IssueSeverity.ERROR,
                message="URL threat lookup failed",
                details={"email_id": email_context.email_id, "error": str(exc), **evidence},
            )
            return AnalyzerOutput(
                analyzer_name=self.name,
                enabled=True,
                status=AnalyzerExecutionStatus.ERROR,
                score=0,
                severity=SeverityLevel.INFO,
                summary="URL analysis provider failed",
                signals=["url_provider_error"],
                evidence={"error": str(exc), **evidence},
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
            summary="URLs inspected by threat intelligence",
            signals=hits,
            evidence=evidence,
        )
