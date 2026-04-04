from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.recorder import record_audit_log
from app.core.deps import get_db_session
from app.core.exceptions import AppException
from app.core.security import require_admin_token
from app.models.enums import AuditEventType
from app.schemas.rule import RuleCreate, RuleRead, RuleUpdate
from app.services.rule_service import RuleService

router = APIRouter(dependencies=[Depends(require_admin_token)])
rule_service = RuleService()


@router.get("", response_model=list[RuleRead])
async def list_rules(session: AsyncSession = Depends(get_db_session)) -> list[RuleRead]:
    rules = await rule_service.list_rules(session)
    return [RuleRead.model_validate(rule) for rule in rules]


@router.post("", response_model=RuleRead)
async def create_rule(payload: RuleCreate, session: AsyncSession = Depends(get_db_session)) -> RuleRead:
    rule = await rule_service.create_rule(session, payload)
    await record_audit_log(
        session,
        event_type=AuditEventType.RULE_CREATED,
        actor="admin",
        resource_type="rule",
        resource_id=rule.id,
        message="Rule created",
        details=payload.model_dump(),
    )
    return RuleRead.model_validate(rule)


@router.put("/{rule_id}", response_model=RuleRead)
async def update_rule(rule_id: str, payload: RuleUpdate, session: AsyncSession = Depends(get_db_session)) -> RuleRead:
    rule = await rule_service.get_rule(session, rule_id)
    if rule is None:
        raise AppException(status_code=404, code="rule_not_found", message="Rule not found")
    updated = await rule_service.update_rule(session, rule, payload)
    await record_audit_log(
        session,
        event_type=AuditEventType.RULE_UPDATED,
        actor="admin",
        resource_type="rule",
        resource_id=rule.id,
        message="Rule updated",
        details=payload.model_dump(exclude_unset=True),
    )
    return RuleRead.model_validate(updated)

