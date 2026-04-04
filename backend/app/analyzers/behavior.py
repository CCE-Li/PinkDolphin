from sqlalchemy import select

from app.analyzers.base import BaseAnalyzer
from app.integrations.sandbox import MockSandboxAdapter
from app.models.contact_history import ContactHistory
from app.models.enums import SeverityLevel
from app.schemas.analysis import AnalyzerOutput
from app.services.context import EmailAnalysisContext


class BehaviorAnalyzer(BaseAnalyzer):
    name = "behavior"

    def __init__(self) -> None:
        self.sandbox = MockSandboxAdapter()

    async def analyze(self, email_context: EmailAnalysisContext) -> AnalyzerOutput:
        sender = email_context.parsed_email.from_email or ""
        recipients = [recipient.email for recipient in email_context.parsed_email.to_recipients]
        score = 0
        signals: list[str] = []

        for recipient in recipients:
            stmt = select(ContactHistory).where(
                ContactHistory.sender_email == sender.lower(),
                ContactHistory.recipient_email == recipient.lower(),
            )
            history = (await email_context.session.execute(stmt)).scalar_one_or_none()
            if history is None:
                score += 10
                signals.append(f"new_contact:{recipient}")

        sandbox_result = self.sandbox.inspect_behavior(
            subject=email_context.parsed_email.subject,
            body_text=email_context.parsed_email.body_text,
        )
        score += int(sandbox_result["score"])
        signals.extend(sandbox_result["hits"])  # type: ignore[arg-type]

        severity = SeverityLevel.LOW
        if score >= 50:
            severity = SeverityLevel.HIGH
        elif score >= 20:
            severity = SeverityLevel.MEDIUM

        return AnalyzerOutput(
            analyzer_name=self.name,
            score=score,
            severity=severity,
            summary="Contact history and mock behavior signals evaluated",
            signals=signals,
            evidence={"sender": sender, "recipients": recipients},
        )

