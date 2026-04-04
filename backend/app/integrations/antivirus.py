import asyncio
import base64
from typing import Any

import httpx

from app.core.config import get_settings


class MockAntivirusAdapter:
    def scan_attachment(self, filename: str | None, content_type: str | None, size: int) -> dict[str, object]:
        score = 0
        hits: list[str] = []
        lowered = (filename or "").lower()
        if lowered.endswith((".exe", ".js", ".scr", ".bat")):
            score += 50
            hits.append("executable_extension")
        if lowered.endswith(".zip"):
            score += 20
            hits.append("archive_attachment")
        if content_type and "macro" in content_type.lower():
            score += 40
            hits.append("macro_content_type")
        if size > 5 * 1024 * 1024:
            score += 10
            hits.append("large_attachment")
        return {"score": score, "hits": hits, "provider": "mock"}


class VirusTotalAdapter:
    base_url = "https://www.virustotal.com/api/v3"

    def __init__(self) -> None:
        self.settings = get_settings()

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "x-apikey": self.settings.virustotal_api_key or "",
        }

    async def scan_attachment(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        size: int,
        sha256: str | None,
        content_base64: str | None,
    ) -> dict[str, object]:
        if not sha256:
            raise RuntimeError("Attachment sha256 is missing")

        report = await self._get_file_report(sha256)
        uploaded = False
        analysis_summary: dict[str, Any] | None = None

        if report is None and self.settings.virustotal_upload_enabled and content_base64:
            analysis_id = await self._upload_file(filename=filename, content_type=content_type, content_base64=content_base64)
            analysis_summary = await self._poll_analysis(analysis_id)
            report = await self._get_file_report(sha256)
            uploaded = True

        if report is None:
            return {
                "score": 5 if size > 0 else 0,
                "hits": ["virustotal_report_missing"],
                "provider": "virustotal",
                "filename": filename,
                "sha256": sha256,
                "uploaded": uploaded,
                "analysis_summary": analysis_summary,
            }

        return self._summarize_report(
            report,
            filename=filename,
            sha256=sha256,
            uploaded=uploaded,
            analysis_summary=analysis_summary,
        )

    async def _get_file_report(self, sha256: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(timeout=self.settings.virustotal_timeout_seconds) as client:
            response = await client.get(f"{self.base_url}/files/{sha256}", headers=self._headers)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()

    async def _upload_file(self, *, filename: str | None, content_type: str | None, content_base64: str) -> str:
        payload = base64.b64decode(content_base64)
        files = {
            "file": (
                filename or "attachment.bin",
                payload,
                content_type or "application/octet-stream",
            )
        }
        async with httpx.AsyncClient(timeout=self.settings.virustotal_timeout_seconds) as client:
            response = await client.post(f"{self.base_url}/files", headers={"x-apikey": self.settings.virustotal_api_key or ""}, files=files)
        response.raise_for_status()
        data = response.json()
        return str(data["data"]["id"])

    async def _poll_analysis(self, analysis_id: str) -> dict[str, Any]:
        summary: dict[str, Any] = {"status": "queued", "stats": {}}
        async with httpx.AsyncClient(timeout=self.settings.virustotal_timeout_seconds) as client:
            for _ in range(max(self.settings.virustotal_poll_attempts, 1)):
                response = await client.get(f"{self.base_url}/analyses/{analysis_id}", headers=self._headers)
                response.raise_for_status()
                data = response.json()
                attrs = data.get("data", {}).get("attributes", {})
                summary = {
                    "status": attrs.get("status", "unknown"),
                    "stats": attrs.get("stats", {}),
                }
                if summary["status"] == "completed":
                    break
                await asyncio.sleep(max(self.settings.virustotal_poll_interval_seconds, 1))
        return summary

    def _summarize_report(
        self,
        report: dict[str, Any],
        *,
        filename: str | None,
        sha256: str,
        uploaded: bool,
        analysis_summary: dict[str, Any] | None,
    ) -> dict[str, object]:
        attrs = report.get("data", {}).get("attributes", {})
        stats = attrs.get("last_analysis_stats", {})
        results = attrs.get("last_analysis_results", {}) or {}
        malicious = int(stats.get("malicious", 0) or 0)
        suspicious = int(stats.get("suspicious", 0) or 0)
        harmless = int(stats.get("harmless", 0) or 0)

        score = min(malicious * 15 + suspicious * 8, 100)
        hits: list[str] = []
        if malicious:
            hits.append(f"virustotal_malicious:{malicious}")
        if suspicious:
            hits.append(f"virustotal_suspicious:{suspicious}")
        if not hits and harmless:
            hits.append("virustotal_clean")

        detections: list[dict[str, str | None]] = []
        for engine, item in results.items():
            category = str(item.get("category") or "")
            if category not in {"malicious", "suspicious"}:
                continue
            detections.append(
                {
                    "engine": engine,
                    "category": category,
                    "result": item.get("result"),
                }
            )
            if len(detections) >= 10:
                break

        return {
            "score": score,
            "hits": hits,
            "provider": "virustotal",
            "filename": filename,
            "sha256": sha256,
            "uploaded": uploaded,
            "analysis_summary": analysis_summary,
            "last_analysis_stats": stats,
            "detections": detections,
            "meaningful_name": attrs.get("meaningful_name"),
            "type_description": attrs.get("type_description"),
            "times_submitted": attrs.get("times_submitted"),
        }


class AntivirusGateway:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.mock = MockAntivirusAdapter()
        self.virustotal = VirusTotalAdapter() if self.settings.virustotal_api_key else None

    async def scan_attachment(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        size: int,
        sha256: str | None,
        content_base64: str | None,
    ) -> dict[str, object]:
        if self.settings.attachment_scan_provider == "virustotal":
            if self.virustotal is None:
                raise RuntimeError("VIRUSTOTAL_API_KEY is not configured")
            return await self.virustotal.scan_attachment(
                filename=filename,
                content_type=content_type,
                size=size,
                sha256=sha256,
                content_base64=content_base64,
            )
        return self.mock.scan_attachment(filename=filename, content_type=content_type, size=size)
