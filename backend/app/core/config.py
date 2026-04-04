from functools import lru_cache
import json
from pathlib import Path
from typing import Annotated
from typing import Any
from typing import cast

from pydantic import Field, field_validator
from pydantic_settings import NoDecode
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Phishing Mail Backend"
    app_env: str = "local"
    api_v1_prefix: str = "/api"
    cors_allow_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
        ]
    )
    cors_allow_origin_regex: str = (
        r"^https?://("
        r"localhost|127\.0\.0\.1|"
        r"10(?:\.\d{1,3}){3}|"
        r"192\.168(?:\.\d{1,3}){2}|"
        r"172\.(?:1[6-9]|2\d|3[0-1])(?:\.\d{1,3}){2}"
        r")(?::(5173|4173))?$"
    )
    admin_bearer_token: str = "change-me"
    database_url: str = "postgresql+psycopg://phishing:phishing@localhost:5432/phishing_mail"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    max_upload_size_mb: int = 10
    log_level: str = "INFO"
    auto_migrate_on_startup: bool = True
    auto_ingest_enabled: bool = True
    auto_ingest_poll_seconds: int = 15
    local_inbox_dir: str = "sample_data/inbox"
    local_processed_dir: str = "sample_data/processed"
    local_failed_dir: str = "sample_data/failed"
    mailbox_listener_enabled: bool = True
    mailbox_listener_refresh_seconds: int = 30
    mailbox_listener_retry_seconds: int = 10
    mailbox_default_poll_seconds: int = 5
    mailbox_credentials_secret: str = "change-me-mailbox-secret"
    privacy_skip_url_on_sender_allowlist: bool = False
    privacy_skip_attachment_on_sender_allowlist: bool = False
    privacy_skip_llm_on_sender_allowlist: bool = False
    url_scan_provider: str = "mock"
    safebrowsing_api_key: str | None = None
    safebrowsing_timeout_seconds: int = 10
    attachment_scan_provider: str = "mock"
    virustotal_api_key: str | None = None
    virustotal_timeout_seconds: int = 30
    virustotal_poll_attempts: int = 4
    virustotal_poll_interval_seconds: int = 4
    virustotal_upload_enabled: bool = False
    llm_analyzer_enabled: bool = False
    llm_provider_mode: str = "mock"
    llm_model: str = "gpt-4.1-mini"
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_timeout_seconds: int = 8
    llm_max_input_chars: int = 6000
    llm_temperature: float = 0.0
    analyzer_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "header_auth": 1.0,
            "content_rule": 1.2,
            "url": 1.3,
            "attachment": 1.1,
            "behavior": 0.9,
            "llm": 0.8,
        }
    )
    enabled_analyzers: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["header_auth", "content_rule", "url", "attachment", "behavior", "llm"]
    )

    @field_validator("enabled_analyzers", mode="before")
    @classmethod
    def parse_enabled_analyzers(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                parsed = json.loads(stripped)
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in value.split(",") if item.strip()]
        return cast(list[str], value)

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_allow_origins(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return cast(list[str], value)

    @property
    def inbox_path(self) -> Path:
        return Path(self.local_inbox_dir)

    @property
    def processed_path(self) -> Path:
        return Path(self.local_processed_dir)

    @property
    def failed_path(self) -> Path:
        return Path(self.local_failed_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
