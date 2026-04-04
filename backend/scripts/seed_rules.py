import asyncio

from sqlalchemy import select

from app.db.session import db_manager
from app.models.rule import Rule
from app.models.enums import RecommendedAction, RuleConditionType, RuleSeverity


async def main() -> None:
    async with db_manager.session() as session:
        existing = await session.execute(select(Rule).where(Rule.name == "Urgent Credential Reset"))
        if existing.scalar_one_or_none() is None:
            session.add(
                Rule(
                    name="Urgent Credential Reset",
                    description="Flag urgent credential reset wording",
                    condition_type=RuleConditionType.BODY_CONTAINS,
                    condition_value="password reset",
                    score_modifier=25,
                    severity=RuleSeverity.HIGH,
                    override_action=RecommendedAction.MANUAL_REVIEW,
                )
            )


if __name__ == "__main__":
    asyncio.run(main())

