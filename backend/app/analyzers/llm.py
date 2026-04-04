from app.analyzers.base import BaseAnalyzer
from app.models.enums import AnalyzerExecutionStatus, SeverityLevel
from app.integrations.llm import LLMAnalysisGateway
from app.schemas.analysis import AnalyzerOutput
from app.services.context import EmailAnalysisContext
from app.services.llm_prompt_service import LLMPromptService


class LLMAnalyzer(BaseAnalyzer):
    name = "llm"

    def __init__(self) -> None:
        self.prompt_service = LLMPromptService()
        self.gateway = LLMAnalysisGateway()

    async def analyze(self, email_context: EmailAnalysisContext) -> AnalyzerOutput:
        if not email_context.allow_llm:
            return AnalyzerOutput(
                analyzer_name=self.name,
                enabled=False,
                status=AnalyzerExecutionStatus.SKIPPED,
                score=0,
                severity=SeverityLevel.INFO,
                summary="LLM skipped due to privacy allowlist policy",
                signals=["privacy_allowlist_skip"],
                evidence={"allowlist_hits": email_context.privacy_allowlist_hits},
            )
        messages = self.prompt_service.build_messages(email_context.parsed_email)
        return await self.gateway.analyze(messages)
