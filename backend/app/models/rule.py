from sqlalchemy import Boolean, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import RecommendedAction, RuleConditionType, RuleSeverity, sql_enum
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Rule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "rules"
    __table_args__ = (
        Index("ix_rules_is_active", "is_active"),
        Index("ix_rules_condition_type", "condition_type"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    condition_type: Mapped[RuleConditionType] = mapped_column(
        sql_enum(RuleConditionType),
        nullable=False,
    )
    condition_value: Mapped[str] = mapped_column(String(1024), nullable=False)
    score_modifier: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    severity: Mapped[RuleSeverity] = mapped_column(sql_enum(RuleSeverity), nullable=False)
    override_action: Mapped[RecommendedAction | None] = mapped_column(
        sql_enum(RecommendedAction),
        nullable=True,
    )
