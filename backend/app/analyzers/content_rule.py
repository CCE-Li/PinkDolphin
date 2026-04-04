from app.analyzers.base import BaseAnalyzer
from app.models.enums import SeverityLevel
from app.schemas.analysis import AnalyzerOutput
from app.services.context import EmailAnalysisContext


class ContentRuleAnalyzer(BaseAnalyzer):
    name = "content_rule"

    async def analyze(self, email_context: EmailAnalysisContext) -> AnalyzerOutput:
        text = f"{email_context.parsed_email.subject or ''} {email_context.parsed_email.body_text or ''}".lower()
        suspicious_terms = ("urgent", "verify", "password", "gift card", "invoice", "bank")
        hits = [term for term in suspicious_terms if term in text]
        score = len(hits) * 10

        for rule in email_context.matched_rules:
            if rule.condition_type.value in {"subject_contains", "body_contains"}:
                score += rule.score_modifier

        severity = SeverityLevel.LOW
        if score >= 50:
            severity = SeverityLevel.HIGH
        elif score >= 20:
            severity = SeverityLevel.MEDIUM

        return AnalyzerOutput(
            analyzer_name=self.name,
            score=score,
            severity=severity,
            summary="Content keywords and custom rules evaluated",
            signals=hits,
            evidence={"matched_rules": [rule.name for rule in email_context.matched_rules]},
        )

