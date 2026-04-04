import asyncio
import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings
from app.core.exceptions import DeferredAnalysisError
from app.models.enums import AnalyzerExecutionStatus, IssueSeverity, SeverityLevel
from app.schemas.analysis import AnalyzerOutput
from app.services.issue_log_service import IssueLogService


class MockLLMAdapter:
    async def analyze(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        content = " ".join(message["content"] for message in messages).lower()
        signals: list[str] = []
        score = 0
        if "password" in content:
            score += 20
            signals.append("credential_request_language")
        if "gift card" in content:
            score += 25
            signals.append("gift_card_language")
        if "login" in content:
            score += 15
            signals.append("login_lure")
        if "spf=fail" in content or "dkim=fail" in content or "dmarc=fail" in content:
            score += 20
            signals.append("auth_failure_context")

        severity = SeverityLevel.LOW
        if score >= 70:
            severity = SeverityLevel.CRITICAL
        elif score >= 50:
            severity = SeverityLevel.HIGH
        elif score >= 25:
            severity = SeverityLevel.MEDIUM

        return {
            "score": min(score, 100),
            "severity": severity.value,
            "summary": "Mock LLM analyzed semantic phishing patterns",
            "signals": signals,
            "evidence": {"mode": "mock"},
        }


class OpenAICompatibleLLMAdapter:
    def __init__(self) -> None:
        settings = get_settings()
        client_kwargs: dict[str, Any] = {"api_key": settings.llm_api_key}
        if settings.llm_base_url:
            client_kwargs["base_url"] = settings.llm_base_url
        self.client = AsyncOpenAI(**client_kwargs)
        self.settings = settings

    async def analyze(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=self.settings.llm_model,
                messages=messages,
                temperature=self.settings.llm_temperature,
                response_format={"type": "json_object"},
            ),
            timeout=self.settings.llm_timeout_seconds,
        )
        raw_content = response.choices[0].message.content or "{}"
        parsed = json.loads(raw_content)
        if isinstance(parsed, dict):
            parsed["_meta_raw_content_preview"] = raw_content[:1000]
        return parsed


class LLMAnalysisGateway:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.mock_adapter = MockLLMAdapter()
        self.real_adapter = OpenAICompatibleLLMAdapter() if self.settings.llm_api_key else None
        self.issue_log_service = IssueLogService()

    async def analyze(self, messages: list[dict[str, str]]) -> AnalyzerOutput:
        if not self.settings.llm_analyzer_enabled:
            await self.issue_log_service.log_detached(
                component="analyzer:llm",
                severity=IssueSeverity.INFO,
                message="LLM analyzer disabled",
                details={"mode": "disabled"},
            )
            return AnalyzerOutput(
                analyzer_name="llm",
                enabled=False,
                status=AnalyzerExecutionStatus.SKIPPED,
                score=0,
                severity=SeverityLevel.INFO,
                summary="LLM analyzer disabled",
                signals=[],
                evidence={"mode": "disabled"},
            )

        try:
            if self.settings.llm_provider_mode == "real":
                await self.issue_log_service.log_detached(
                    component="analyzer:llm",
                    severity=IssueSeverity.INFO,
                    message="LLM real request started",
                    details={
                        "provider_mode": self.settings.llm_provider_mode,
                        "model": self.settings.llm_model,
                        "base_url": self.settings.llm_base_url,
                        "message_count": len(messages),
                        "prompt_chars": sum(len(item.get("content", "")) for item in messages),
                    },
                )
                if self.real_adapter is None:
                    raise RuntimeError("LLM_API_KEY is not configured")
                result = await self.real_adapter.analyze(messages)
                mode = "real"
            else:
                result = await asyncio.wait_for(
                    self.mock_adapter.analyze(messages),
                    timeout=self.settings.llm_timeout_seconds,
                )
                mode = "mock"
        except Exception as exc:
            await self.issue_log_service.log_detached(
                component="analyzer:llm",
                severity=IssueSeverity.ERROR,
                message="LLM real request failed, analysis deferred",
                details={
                    "provider_mode": self.settings.llm_provider_mode,
                    "model": self.settings.llm_model,
                    "base_url": self.settings.llm_base_url,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            raise DeferredAnalysisError("analyzer:llm", f"LLM real request failed: {type(exc).__name__}") from exc

        raw_content_preview = None
        if isinstance(result, dict):
            raw_content_preview = result.pop("_meta_raw_content_preview", None)
        await self.issue_log_service.log_detached(
            component="analyzer:llm",
            severity=IssueSeverity.INFO,
            message="LLM real request completed" if mode == "real" else "LLM mock analysis completed",
            details={
                "provider_mode": self.settings.llm_provider_mode,
                "model": self.settings.llm_model,
                "base_url": self.settings.llm_base_url,
                "score": result.get("score", 0),
                "severity": result.get("severity", SeverityLevel.INFO.value),
                "summary": result.get("summary", "LLM analysis completed"),
                "signals": list(result.get("signals", [])),
                "raw_content_preview": raw_content_preview,
            },
        )
        return AnalyzerOutput(
            analyzer_name="llm",
            enabled=True,
            status=AnalyzerExecutionStatus.SUCCESS,
            score=max(0, min(int(result.get("score", 0)), 100)),
            severity=SeverityLevel(str(result.get("severity", SeverityLevel.INFO.value))),
            summary=str(result.get("summary", "LLM analysis completed")),
            signals=list(result.get("signals", [])),
            evidence={**dict(result.get("evidence", {})), "mode": mode, "model": self.settings.llm_model},
        )
