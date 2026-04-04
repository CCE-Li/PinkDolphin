from pydantic import BaseModel

from app.models.enums import RecommendedAction, RuleConditionType, RuleSeverity
from app.schemas.common import TimestampedSchema


class RuleCreate(BaseModel):
    name: str
    description: str | None = None
    is_active: bool = True
    condition_type: RuleConditionType
    condition_value: str
    score_modifier: int = 0
    severity: RuleSeverity = RuleSeverity.MEDIUM
    override_action: RecommendedAction | None = None


class RuleUpdate(BaseModel):
    description: str | None = None
    is_active: bool | None = None
    condition_value: str | None = None
    score_modifier: int | None = None
    severity: RuleSeverity | None = None
    override_action: RecommendedAction | None = None


class RuleRead(TimestampedSchema):
    name: str
    description: str | None
    is_active: bool
    condition_type: RuleConditionType
    condition_value: str
    score_modifier: int
    severity: RuleSeverity
    override_action: RecommendedAction | None

