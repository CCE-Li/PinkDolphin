from sqlalchemy.ext.asyncio import AsyncSession

from app.analyzers.registry import get_enabled_analyzers
from app.audit.recorder import record_audit_log
from app.models.analysis import AnalysisResult, AnalyzerResult
from app.models.email import Email
from app.models.enums import AuditEventType, EmailStatus, IssueSeverity, RecommendedAction, RiskLevel
from app.schemas.analysis import AnalyzerOutput
from app.schemas.email import EmailAnalyzeResponse, ParsedEmailSchema
from app.services.allowlist_service import AllowlistService
from app.services.context import EmailAnalysisContext
from app.services.decision_engine import DecisionEngine
from app.services.incident_service import IncidentService
from app.services.issue_log_service import IssueLogService
from app.services.rule_service import RuleService


class AnalysisEngine:
    def __init__(self) -> None:
        self.allowlist_service = AllowlistService()
        self.rule_service = RuleService()
        self.decision_engine = DecisionEngine()
        self.incident_service = IncidentService()
        self.issue_log_service = IssueLogService()

    async def analyze_email(
        self,
        session: AsyncSession,
        *,
        email: Email,
        parsed_email: ParsedEmailSchema,
        actor: str,
        event_type: AuditEventType,
    ) -> EmailAnalyzeResponse:
        enabled_analyzers = get_enabled_analyzers()
        await self.issue_log_service.log(
            session,
            component="analysis:email",
            severity=IssueSeverity.INFO,
            message="Email analysis started",
            details={
                "email_id": email.id,
                "subject": parsed_email.subject,
                "from_email": parsed_email.from_email,
                "mailbox_account_id": email.mailbox_account_id,
                "event_type": event_type.value,
                "enabled_analyzers": [analyzer.name for analyzer in enabled_analyzers],
            },
        )
        matched_rules = await self.rule_service.match_rules(
            session,
            subject=parsed_email.subject,
            body_text=parsed_email.body_text,
            sender_email=parsed_email.from_email,
            links=parsed_email.links,
        )
        allowlist_hits = await self.allowlist_service.match_entries(session, parsed_email)
        sender_allowlist_hits = await self.allowlist_service.match_sender_entries(session, parsed_email)
        sender_allowlist_matched = bool(sender_allowlist_hits)
        skip_url = sender_allowlist_matched and any(item.skip_url_scan for item in sender_allowlist_hits)
        skip_attachment = sender_allowlist_matched and any(item.skip_attachment_scan for item in sender_allowlist_hits)
        skip_llm = sender_allowlist_matched and any(item.skip_llm_scan for item in sender_allowlist_hits)
        allow_url = not skip_url
        allow_attachment = not skip_attachment
        allow_llm = not skip_llm
        context = EmailAnalysisContext(
            email_id=email.id,
            session=session,
            parsed_email=parsed_email,
            matched_rules=matched_rules,
            sender_allowlist_matched=sender_allowlist_matched,
            sender_allowlist_hits=sender_allowlist_hits,
            allow_url=allow_url,
            allow_attachment=allow_attachment,
            allow_llm=allow_llm,
            privacy_allowlist_hits=[
                {"id": item.id, "list_type": item.list_type.value, "value": item.value}
                for item in allowlist_hits
            ],
        )
        if context.privacy_allowlist_hits:
            await self.issue_log_service.log(
                session,
                component="analysis:email",
                severity=IssueSeverity.WARNING,
                message="Privacy allowlist matched",
                details={
                    "email_id": email.id,
                    "allowlist_hits": context.privacy_allowlist_hits,
                    "sender_allowlist_matched": sender_allowlist_matched,
                    "sender_allowlist_controls": [
                        {
                            "id": item.id,
                            "value": item.value,
                            "skip_url_scan": item.skip_url_scan,
                            "skip_attachment_scan": item.skip_attachment_scan,
                            "skip_llm_scan": item.skip_llm_scan,
                        }
                        for item in sender_allowlist_hits
                    ],
                },
            )
        analyzer_outputs: list[AnalyzerOutput] = []
        for analyzer in enabled_analyzers:
            analyzer_outputs.append(await analyzer.analyze(context))

        for output in analyzer_outputs:
            severity = IssueSeverity.INFO
            if output.status.value == "error":
                severity = IssueSeverity.ERROR
            elif output.status.value == "skipped":
                severity = IssueSeverity.WARNING
            await self.issue_log_service.log(
                session,
                component=f"analyzer:{output.analyzer_name}",
                severity=severity,
                message=output.summary,
                details={
                    "email_id": email.id,
                    "status": output.status.value,
                    "score": output.score,
                    "severity": output.severity.value,
                    "signals": output.signals,
                    "evidence": output.evidence,
                },
            )

        all_sensitive_analyzers_skipped = sender_allowlist_matched and not allow_url and not allow_attachment and not allow_llm
        if all_sensitive_analyzers_skipped:
            decision = {
                "total_score": 0,
                "risk_level": RiskLevel.LOW,
                "recommended_action": RecommendedAction.ALLOW,
                "override_reason": "privacy_sender_allowlist_full_skip",
                "summary": "Sender allowlist matched and privacy policy bypassed URL, attachment, and LLM analysis",
                "decision_details": {
                    "weighted_breakdown": {},
                    "matched_rules": [rule.name for rule in matched_rules],
                    "privacy_safe_short_circuit": True,
                    "sender_allowlist_hits": [
                        {"id": item.id, "list_type": item.list_type.value, "value": item.value}
                        for item in sender_allowlist_hits
                    ],
                },
            }
        else:
            decision = self.decision_engine.evaluate(analyzer_outputs, matched_rules)
        await self.issue_log_service.log(
            session,
            component="analysis:decision",
            severity=IssueSeverity.INFO,
            message="Email risk decision generated",
            details={
                "email_id": email.id,
                "total_score": decision["total_score"],
                "risk_level": decision["risk_level"].value,
                "recommended_action": decision["recommended_action"].value,
                "override_reason": decision["override_reason"],
                "decision_details": decision["decision_details"],
            },
        )
        analysis_result = AnalysisResult(
            email_id=email.id,
            total_score=decision["total_score"],
            risk_level=decision["risk_level"],
            recommended_action=decision["recommended_action"],
            summary=decision["summary"],
            override_reason=decision["override_reason"],
            decision_details=decision["decision_details"],
        )
        session.add(analysis_result)
        await session.flush()

        for output in analyzer_outputs:
            session.add(
                AnalyzerResult(
                    analysis_result_id=analysis_result.id,
                    analyzer_name=output.analyzer_name,
                    enabled=output.enabled,
                    status=output.status,
                    score=output.score,
                    severity=output.severity,
                    summary=output.summary,
                    signals=output.signals,
                    evidence=output.evidence,
                )
            )

        email.status = EmailStatus.ANALYZED
        email.latest_analysis_id = analysis_result.id
        email.latest_risk_level = decision["risk_level"].value
        email.latest_score = decision["total_score"]

        await self.incident_service.ensure_incident_for_risky_email(session, email=email, analysis_result=analysis_result)
        await record_audit_log(
            session,
            event_type=event_type,
            actor=actor,
            resource_type="email",
            resource_id=email.id,
            message=f"Email analyzed with risk {decision['risk_level'].value}",
            details={
                "analysis_id": analysis_result.id,
                "recommended_action": decision["recommended_action"].value,
                "total_score": decision["total_score"],
                "privacy_allowlist_hits": context.privacy_allowlist_hits,
                "analyzers": [
                    {
                        "name": output.analyzer_name,
                        "status": output.status.value,
                        "score": output.score,
                        "severity": output.severity.value,
                    }
                    for output in analyzer_outputs
                ],
            },
        )
        await session.flush()
        return EmailAnalyzeResponse(
            email_id=email.id,
            analysis_id=analysis_result.id,
            risk_level=decision["risk_level"],
            recommended_action=decision["recommended_action"],
            total_score=decision["total_score"],
            analyzer_results=analyzer_outputs,
        )
