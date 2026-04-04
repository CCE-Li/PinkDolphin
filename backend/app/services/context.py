from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rule import Rule
from app.schemas.email import ParsedEmailSchema
from app.models.list_entry import Allowlist


@dataclass(slots=True)
class EmailAnalysisContext:
    email_id: str
    session: AsyncSession
    parsed_email: ParsedEmailSchema
    matched_rules: list[Rule] = field(default_factory=list)
    sender_allowlist_matched: bool = False
    sender_allowlist_hits: list[Allowlist] = field(default_factory=list)
    allow_url: bool = True
    allow_attachment: bool = True
    allow_llm: bool = True
    privacy_allowlist_hits: list[dict[str, str]] = field(default_factory=list)
