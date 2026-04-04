from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.list_entry import Allowlist
from app.models.enums import ListType
from app.schemas.allowlist import AllowlistCreate, AllowlistUpdate
from app.schemas.email import ParsedEmailSchema
from app.utils.email import extract_domain_from_email, normalize_email_address


class AllowlistService:
    async def list_entries(self, session: AsyncSession) -> list[Allowlist]:
        result = await session.execute(select(Allowlist).order_by(Allowlist.created_at.desc()))
        return list(result.scalars().all())

    async def get_entry(self, session: AsyncSession, entry_id: str) -> Allowlist:
        entry = await session.get(Allowlist, entry_id)
        if entry is None:
            raise AppException(status_code=404, code="allowlist_not_found", message="Allowlist entry not found")
        return entry

    async def create_entry(self, session: AsyncSession, payload: AllowlistCreate) -> Allowlist:
        normalized = self._normalize_value(payload.list_type, payload.value)
        await self._ensure_unique_value(session, normalized)
        entry = Allowlist(
            list_type=payload.list_type,
            value=normalized,
            is_active=payload.is_active,
            skip_url_scan=payload.skip_url_scan,
            skip_attachment_scan=payload.skip_attachment_scan,
            skip_llm_scan=payload.skip_llm_scan,
        )
        session.add(entry)
        await session.flush()
        return entry

    async def update_entry(self, session: AsyncSession, entry: Allowlist, payload: AllowlistUpdate) -> Allowlist:
        next_list_type = payload.list_type or entry.list_type
        next_value = self._normalize_value(next_list_type, payload.value if payload.value is not None else entry.value)
        if next_value != entry.value:
            await self._ensure_unique_value(session, next_value)
        entry.list_type = next_list_type
        entry.value = next_value
        if payload.is_active is not None:
            entry.is_active = payload.is_active
        if payload.skip_url_scan is not None:
            entry.skip_url_scan = payload.skip_url_scan
        if payload.skip_attachment_scan is not None:
            entry.skip_attachment_scan = payload.skip_attachment_scan
        if payload.skip_llm_scan is not None:
            entry.skip_llm_scan = payload.skip_llm_scan
        await session.flush()
        return entry

    async def match_entries(self, session: AsyncSession, parsed_email: ParsedEmailSchema) -> list[Allowlist]:
        result = await session.execute(select(Allowlist).where(Allowlist.is_active.is_(True)))
        entries = list(result.scalars().all())
        if not entries:
            return []

        sender_email = normalize_email_address(parsed_email.from_email)
        sender_domain = extract_domain_from_email(parsed_email.from_email)
        link_urls: set[str] = set()
        for url in parsed_email.links:
            try:
                normalized = self._normalize_url(url)
            except AppException:
                continue
            if normalized:
                link_urls.add(normalized)
        link_domains = {
            domain
            for domain in (self._extract_url_domain(url) for url in parsed_email.links)
            if domain
        }

        matches: list[Allowlist] = []
        for entry in entries:
            if entry.list_type == ListType.ADDRESS and sender_email and entry.value == sender_email:
                matches.append(entry)
            elif entry.list_type == ListType.DOMAIN and entry.value in {sender_domain, *link_domains}:
                matches.append(entry)
            elif entry.list_type == ListType.URL and entry.value in link_urls:
                matches.append(entry)
        return matches

    async def match_sender_entries(self, session: AsyncSession, parsed_email: ParsedEmailSchema) -> list[Allowlist]:
        result = await session.execute(select(Allowlist).where(Allowlist.is_active.is_(True)))
        entries = list(result.scalars().all())
        if not entries:
            return []

        sender_email = normalize_email_address(parsed_email.from_email)
        sender_domain = extract_domain_from_email(parsed_email.from_email)

        matches: list[Allowlist] = []
        for entry in entries:
            if entry.list_type == ListType.ADDRESS and sender_email and entry.value == sender_email:
                matches.append(entry)
            elif entry.list_type == ListType.DOMAIN and sender_domain and entry.value == sender_domain:
                matches.append(entry)
        return matches

    async def _ensure_unique_value(self, session: AsyncSession, value: str) -> None:
        existing = (await session.execute(select(Allowlist.id).where(Allowlist.value == value))).scalar_one_or_none()
        if existing is not None:
            raise AppException(status_code=409, code="allowlist_exists", message="Allowlist value already exists")

    def _normalize_value(self, list_type: ListType, value: str) -> str:
        raw = value.strip()
        if not raw:
            raise AppException(status_code=400, code="allowlist_value_required", message="Allowlist value is required")
        if list_type == ListType.ADDRESS:
            normalized = normalize_email_address(raw)
            if not normalized:
                raise AppException(status_code=400, code="invalid_allowlist_address", message="Invalid email address")
            return normalized
        if list_type == ListType.DOMAIN:
            return raw.lower().lstrip("@")
        if list_type == ListType.URL:
            return self._normalize_url(raw) or raw.lower()
        return raw.lower()

    def _normalize_url(self, value: str) -> str | None:
        raw = value.strip()
        if not raw:
            return None
        parsed = urlparse(raw)
        if not parsed.scheme or not parsed.netloc:
            raise AppException(status_code=400, code="invalid_allowlist_url", message="Invalid allowlist URL")
        normalized_path = parsed.path or "/"
        normalized_query = f"?{parsed.query}" if parsed.query else ""
        return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{normalized_path}{normalized_query}"

    def _extract_url_domain(self, value: str) -> str | None:
        parsed = urlparse(value)
        domain = (parsed.hostname or "").strip().lower()
        return domain or None
