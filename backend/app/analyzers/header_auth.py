from app.analyzers.base import BaseAnalyzer
from app.models.enums import SeverityLevel
from app.schemas.analysis import AnalyzerOutput
from app.services.context import EmailAnalysisContext


class HeaderAuthAnalyzer(BaseAnalyzer):
    name = "header_auth"

    async def analyze(self, email_context: EmailAnalysisContext) -> AnalyzerOutput:
        auth_results = (email_context.parsed_email.authentication_results or "").lower()
        score = 0
        signals: list[str] = []

        if "spf=fail" in auth_results:
            score += 25
            signals.append("spf_fail")
        if "dkim=fail" in auth_results:
            score += 25
            signals.append("dkim_fail")
        if "dmarc=fail" in auth_results:
            score += 30
            signals.append("dmarc_fail")
        if not auth_results:
            score += 10
            signals.append("auth_missing")

        severity = SeverityLevel.LOW
        if score >= 50:
            severity = SeverityLevel.HIGH
        elif score >= 20:
            severity = SeverityLevel.MEDIUM

        return AnalyzerOutput(
            analyzer_name=self.name,
            score=score,
            severity=severity,
            summary="Header authentication checks evaluated",
            signals=signals,
            evidence={"authentication_results": email_context.parsed_email.authentication_results},
        )

