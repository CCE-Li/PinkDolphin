from pathlib import Path
import re

from app.core.config import get_settings
from app.schemas.config_management import EnvFileRead


class ConfigManagementService:
    editable_keys = [
        "FRONTEND_APP_URL",
        "BACKEND_PUBLIC_URL",
        "MICROSOFT_TENANT_ID",
        "MICROSOFT_CLIENT_ID",
        "MICROSOFT_CLIENT_SECRET",
        "MICROSOFT_GRAPH_REDIRECT_PATH",
        "MICROSOFT_GRAPH_SCOPES",
        "LOG_LEVEL",
        "MAX_UPLOAD_SIZE_MB",
        "LLM_ANALYZER_ENABLED",
        "LLM_PROVIDER_MODE",
        "LLM_MODEL",
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "LLM_TIMEOUT_SECONDS",
        "LLM_MAX_INPUT_CHARS",
        "LLM_TEMPERATURE",
        "URL_SCAN_PROVIDER",
        "SAFEBROWSING_API_KEY",
        "SAFEBROWSING_TIMEOUT_SECONDS",
        "ATTACHMENT_SCAN_PROVIDER",
        "VIRUSTOTAL_API_KEY",
        "VIRUSTOTAL_TIMEOUT_SECONDS",
        "VIRUSTOTAL_POLL_ATTEMPTS",
        "VIRUSTOTAL_POLL_INTERVAL_SECONDS",
        "VIRUSTOTAL_UPLOAD_ENABLED",
        "ANALYZER_WEIGHTS",
        "ENABLED_ANALYZERS",
    ]

    def __init__(self) -> None:
        self.env_path = Path(__file__).resolve().parents[2] / ".env"

    def read_env_file(self) -> EnvFileRead:
        content = self.env_path.read_text(encoding="utf-8") if self.env_path.exists() else ""
        filtered = self._filter_editable_content(content)
        return EnvFileRead(path=str(self.env_path), content=filtered, editable_keys=self.editable_keys)

    def write_env_file(self, content: str) -> EnvFileRead:
        current = self.env_path.read_text(encoding="utf-8") if self.env_path.exists() else ""
        merged = self._merge_editable_content(current, content)
        self.env_path.write_text(merged, encoding="utf-8")
        get_settings.cache_clear()
        filtered = self._filter_editable_content(merged)
        return EnvFileRead(path=str(self.env_path), content=filtered, editable_keys=self.editable_keys)

    def _filter_editable_content(self, raw: str) -> str:
        editable = set(self.editable_keys)
        current = self._parse_key_values(raw)
        lines: list[str] = []
        seen: set[str] = set()
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            key = stripped.split("=", 1)[0].strip()
            if key in editable:
                lines.append(line)
                seen.add(key)
        for key in self.editable_keys:
            if key not in seen:
                lines.append(f"{key}={current.get(key, '')}")
        return "\n".join(lines)

    def _merge_editable_content(self, existing: str, updated_subset: str) -> str:
        editable = set(self.editable_keys)
        updates = self._parse_key_values(updated_subset)
        existing_lines = existing.splitlines()
        merged_lines: list[str] = []
        seen_editable: set[str] = set()

        for line in existing_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                merged_lines.append(line)
                continue
            key = stripped.split("=", 1)[0].strip()
            if key in editable:
                if key in updates:
                    merged_lines.append(f"{key}={updates[key]}")
                    seen_editable.add(key)
                continue
            merged_lines.append(line)

        for key in self.editable_keys:
            if key in updates and key not in seen_editable:
                merged_lines.append(f"{key}={updates[key]}")

        output = "\n".join(merged_lines).strip()
        return f"{output}\n" if output else ""

    def _parse_key_values(self, raw: str) -> dict[str, str]:
        pairs: dict[str, str] = {}
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue
            key, value = re.split(r"=", line, maxsplit=1)
            key = key.strip()
            if key in self.editable_keys:
                pairs[key] = value.strip()
        return pairs
