from app.models.enums import RecommendedAction, RiskLevel


def score_to_risk_level(score: int) -> RiskLevel:
    if score >= 90:
        return RiskLevel.CRITICAL
    if score >= 60:
        return RiskLevel.HIGH
    if score >= 30:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def risk_level_to_action(risk_level: RiskLevel) -> RecommendedAction:
    if risk_level == RiskLevel.CRITICAL:
        return RecommendedAction.QUARANTINE
    if risk_level == RiskLevel.HIGH:
        return RecommendedAction.MOVE_TO_SPAM
    if risk_level == RiskLevel.MEDIUM:
        return RecommendedAction.BANNER_WARNING
    return RecommendedAction.ALLOW

