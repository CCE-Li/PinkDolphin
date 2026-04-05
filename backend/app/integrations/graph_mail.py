from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx

from app.core.config import get_settings
from app.core.exceptions import AppException


@dataclass(frozen=True, slots=True)
class GraphTokenBundle:
    access_token: str
    refresh_token: str | None
    expires_at: datetime
    scope: str | None


@dataclass(frozen=True, slots=True)
class GraphProfile:
    subject: str
    email_address: str
    display_name: str | None


@dataclass(frozen=True, slots=True)
class GraphDeltaResult:
    messages: list[dict]
    delta_link: str | None


class GraphMailClient:
    AUTHORITY_TEMPLATE = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0"
    GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self) -> None:
        self.settings = get_settings()

    def build_authorization_url(self, state: str) -> str:
        client_id = self._require_setting(self.settings.microsoft_client_id, "microsoft_client_id")
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": self.settings.microsoft_graph_redirect_uri,
            "response_mode": "query",
            "scope": " ".join(self.settings.microsoft_graph_scopes),
            "state": state,
        }
        return f"{self._authority_base}/authorize?{urlencode(params)}"

    async def exchange_code(self, code: str) -> GraphTokenBundle:
        payload = {
            "client_id": self._require_setting(self.settings.microsoft_client_id, "microsoft_client_id"),
            "client_secret": self._require_setting(self.settings.microsoft_client_secret, "microsoft_client_secret"),
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.settings.microsoft_graph_redirect_uri,
            "scope": " ".join(self.settings.microsoft_graph_scopes),
        }
        return await self._token_request(payload)

    async def refresh_access_token(self, refresh_token: str) -> GraphTokenBundle:
        payload = {
            "client_id": self._require_setting(self.settings.microsoft_client_id, "microsoft_client_id"),
            "client_secret": self._require_setting(self.settings.microsoft_client_secret, "microsoft_client_secret"),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scope": " ".join(self.settings.microsoft_graph_scopes),
        }
        return await self._token_request(payload)

    async def get_profile(self, access_token: str) -> GraphProfile:
        data = await self._request_json("GET", f"{self.GRAPH_BASE_URL}/me?$select=id,displayName,mail,userPrincipalName", access_token)
        email_address = data.get("mail") or data.get("userPrincipalName")
        if not email_address:
            raise AppException(status_code=502, code="graph_profile_missing_email", message="Microsoft Graph did not return an email address")
        return GraphProfile(
            subject=str(data.get("id") or email_address),
            email_address=str(email_address).lower(),
            display_name=data.get("displayName"),
        )

    async def delta_messages(self, access_token: str, *, delta_link: str | None, folder_name: str = "inbox") -> GraphDeltaResult:
        url = delta_link or f"{self.GRAPH_BASE_URL}/me/mailFolders/{folder_name}/messages/delta?$select=id,internetMessageId"
        messages: list[dict] = []
        next_url: str | None = url
        final_delta_link: str | None = delta_link
        while next_url:
            data = await self._request_json("GET", next_url, access_token)
            for item in data.get("value", []):
                if "@removed" in item:
                    continue
                messages.append(item)
            next_url = data.get("@odata.nextLink")
            if data.get("@odata.deltaLink"):
                final_delta_link = data.get("@odata.deltaLink")
        return GraphDeltaResult(messages=messages, delta_link=final_delta_link)

    async def fetch_message_mime(self, access_token: str, message_id: str) -> bytes:
        url = f"{self.GRAPH_BASE_URL}/me/messages/{message_id}/$value"
        return await self._request_bytes("GET", url, access_token)

    async def message_exists(self, access_token: str, message_id: str) -> bool:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.GRAPH_BASE_URL}/me/messages/{message_id}?$select=id",
                headers=self._headers(access_token),
            )
        if response.status_code == 404:
            return False
        if response.status_code >= 400:
            raise AppException(status_code=502, code="graph_request_failed", message=response.text)
        return True

    async def delete_message(self, access_token: str, message_id: str) -> None:
        await self._request_empty("DELETE", f"{self.GRAPH_BASE_URL}/me/messages/{message_id}", access_token)

    @property
    def _authority_base(self) -> str:
        return self.AUTHORITY_TEMPLATE.format(tenant=self.settings.microsoft_tenant_id)

    async def _token_request(self, payload: dict[str, str]) -> GraphTokenBundle:
        token_url = f"{self._authority_base}/token"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(token_url, data=payload)
        if response.status_code >= 400:
            raise AppException(status_code=502, code="graph_token_exchange_failed", message=response.text)
        data = response.json()
        expires_in = int(data.get("expires_in") or 3600)
        return GraphTokenBundle(
            access_token=str(data["access_token"]),
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=max(0, expires_in - 60)),
            scope=data.get("scope"),
        )

    async def _request_json(self, method: str, url: str, access_token: str) -> dict:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=self._headers(access_token))
        if response.status_code >= 400:
            raise AppException(status_code=502, code="graph_request_failed", message=response.text)
        return response.json()

    async def _request_bytes(self, method: str, url: str, access_token: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=self._headers(access_token))
        if response.status_code >= 400:
            raise AppException(status_code=502, code="graph_request_failed", message=response.text)
        return response.content

    async def _request_empty(self, method: str, url: str, access_token: str) -> None:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(method, url, headers=self._headers(access_token))
        if response.status_code >= 400:
            raise AppException(status_code=502, code="graph_request_failed", message=response.text)

    @staticmethod
    def _headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def _require_setting(value: str | None, field_name: str) -> str:
        if value:
            return value
        raise AppException(status_code=500, code="graph_oauth_not_configured", message=f"{field_name} is not configured")
