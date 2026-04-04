from app.core.config import get_settings
from app.models.enums import RecommendedAction
from app.models.rule import Rule
from app.policies.scoring import risk_level_to_action, score_to_risk_level
from app.schemas.analysis import AnalyzerOutput


class DecisionEngine:
    def evaluate(
        self,
        analyzer_results: list[AnalyzerOutput],
        matched_rules: list[Rule],
    ) -> dict[str, object]:
        settings = get_settings()
        weighted_breakdown: dict[str, float] = {}
        total = 0.0
        for result in analyzer_results:
            weight = settings.analyzer_weights.get(result.analyzer_name, 1.0)
            weighted_score = result.score * weight
            weighted_breakdown[result.analyzer_name] = weighted_score
            total += weighted_score

        total += sum(rule.score_modifier for rule in matched_rules)
        total_score = max(int(total), 0)
        risk_level = score_to_risk_level(total_score)
        recommended_action = risk_level_to_action(risk_level)
        override_reason: str | None = None

        priority = {
            RecommendedAction.ALLOW: 0,
            RecommendedAction.BANNER_WARNING: 1,
            RecommendedAction.MOVE_TO_SPAM: 2,
            RecommendedAction.MANUAL_REVIEW: 3,
            RecommendedAction.QUARANTINE: 4,
        }
        for rule in matched_rules:
            if rule.override_action and priority[rule.override_action] >= priority[recommended_action]:
                recommended_action = rule.override_action
                override_reason = f"rule:{rule.name}"

        return {
            "total_score": total_score,
            "risk_level": risk_level,
            "recommended_action": recommended_action,
            "override_reason": override_reason,
            "summary": f"Aggregated {len(analyzer_results)} analyzers with score {total_score}",
            "decision_details": {
                "weighted_breakdown": weighted_breakdown,
                "matched_rules": [rule.name for rule in matched_rules],
            },
        }
