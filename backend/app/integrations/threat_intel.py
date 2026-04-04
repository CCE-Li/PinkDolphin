from urllib.parse import urlparse

import httpx

from app.core.config import get_settings


class MockThreatIntelAdapter:
    def lookup_url(self, url: str) -> dict[str, object]:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        suspicious_keywords = ("login", "verify", "secure", "bonus", "gift")
        score = 0
        hits: list[str] = []

        if any(keyword in url.lower() for keyword in suspicious_keywords):
            score += 20
            hits.append("keyword_match")
        if domain.endswith(".zip") or domain.endswith(".top"):
            score += 30
            hits.append("tld_risk")
        if "@" in url:
            score += 20
            hits.append("credential_style_url")

        return {"score": score, "hits": hits, "domain": domain, "provider": "mock"}


class SafeBrowsingAdapter:
    base_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"

    def __init__(self) -> None:
        self.settings = get_settings()

    async def lookup_url(self, url: str) -> dict[str, object]:
        params = {"key": self.settings.safebrowsing_api_key}
        payload = {
            "client": {
                "clientId": "pink-dolphin",
                "clientVersion": "1.0.0",
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        async with httpx.AsyncClient(timeout=self.settings.safebrowsing_timeout_seconds) as client:
            response = await client.post(self.base_url, params=params, json=payload)
            response.raise_for_status()
        data = response.json()
        matches = list(data.get("matches", []))
        score = min(30 * len(matches), 90)
        hits = [f"google_safe_browsing:{item.get('threatType', 'UNKNOWN').lower()}" for item in matches]
        domain = urlparse(url).netloc.lower()
        return {
            "score": score,
            "hits": hits,
            "domain": domain,
            "provider": "google_safe_browsing",
            "matches": matches,
        }


class ThreatIntelGateway:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.mock = MockThreatIntelAdapter()
        self.safe_browsing = SafeBrowsingAdapter() if self.settings.safebrowsing_api_key else None

    async def lookup_url(self, url: str) -> dict[str, object]:
        if self.settings.url_scan_provider == "google_safe_browsing":
            if self.safe_browsing is None:
                raise RuntimeError("SAFEBROWSING_API_KEY is not configured")
            return await self.safe_browsing.lookup_url(url)
        return self.mock.lookup_url(url)
