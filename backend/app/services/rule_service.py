from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleUpdate
from app.utils.email import extract_domain_from_email


class RuleService:
    async def list_rules(self, session: AsyncSession) -> list[Rule]:
        result = await session.execute(select(Rule).order_by(Rule.created_at.desc()))
        return list(result.scalars().all())

    async def create_rule(self, session: AsyncSession, payload: RuleCreate) -> Rule:
        rule = Rule(**payload.model_dump())
        session.add(rule)
        await session.flush()
        return rule

    async def update_rule(self, session: AsyncSession, rule: Rule, payload: RuleUpdate) -> Rule:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)
        await session.flush()
        return rule

    async def get_rule(self, session: AsyncSession, rule_id: str) -> Rule | None:
        return await session.get(Rule, rule_id)

    async def match_rules(
        self,
        session: AsyncSession,
        *,
        subject: str | None,
        body_text: str | None,
        sender_email: str | None,
        links: list[str],
    ) -> list[Rule]:
        result = await session.execute(select(Rule).where(Rule.is_active.is_(True)))
        rules = list(result.scalars().all())
        subject_text = (subject or "").lower()
        body = (body_text or "").lower()
        sender_domain = (extract_domain_from_email(sender_email) or "").lower()
        lowered_links = [link.lower() for link in links]

        matched: list[Rule] = []
        for rule in rules:
            value = rule.condition_value.lower()
            if rule.condition_type.value == "subject_contains" and value in subject_text:
                matched.append(rule)
            elif rule.condition_type.value == "body_contains" and value in body:
                matched.append(rule)
            elif rule.condition_type.value == "sender_domain" and value == sender_domain:
                matched.append(rule)
            elif rule.condition_type.value == "url_contains" and any(value in link for link in lowered_links):
                matched.append(rule)
        return matched
