from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import ActionType, EmailSource, EmailStatus, RecommendedAction, RiskLevel
from app.schemas.analysis import AnalysisResultRead, AnalyzerOutput
from app.schemas.common import TimestampedSchema


class StructuredEmailAddress(BaseModel):
    name: str | None = None
    email: str


class StructuredAttachment(BaseModel):
    filename: str | None = None
    content_type: str | None = None
    content_base64: str | None = None


class EmailAnalyzeRequest(BaseModel):
    raw_email: str | None = None
    structured_email: dict[str, Any] | None = None
    source: EmailSource = EmailSource.API


class EmailActionRequest(BaseModel):
    action_type: ActionType
    reason: str | None = None
    actor: str = "admin"
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ParsedEmailSchema(BaseModel):
    message_id: str | None = None
    subject: str | None = None
    from_name: str | None = None
    from_email: str | None = None
    reply_to: str | None = None
    return_path: str | None = None
    to_recipients: list[StructuredEmailAddress] = Field(default_factory=list)
    cc_recipients: list[StructuredEmailAddress] = Field(default_factory=list)
    authentication_results: str | None = None
    send_time: datetime | None = None
    raw_headers: dict[str, str] = Field(default_factory=dict)
    body_text: str | None = None
    body_html: str | None = None
    links: list[str] = Field(default_factory=list)
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    raw_email: str | None = None


class EmailListItem(TimestampedSchema):
    message_id: str | None
    subject: str | None
    source: EmailSource
    status: EmailStatus
    mailbox_account_id: str | None = None
    mailbox_display_name: str | None = None
    mailbox_email_address: str | None = None
    remote_uid: int | None = None
    latest_risk_level: str | None
    latest_score: int | None
    latest_recommended_action: str | None = None


class EmailDetail(TimestampedSchema):
    message_id: str | None
    subject: str | None
    authentication_results: str | None
    send_time: datetime | None
    raw_headers: dict[str, Any]
    raw_email: str | None
    body_text: str | None
    body_html: str | None
    source: EmailSource
    status: EmailStatus
    mailbox_account_id: str | None
    remote_uid: int | None
    remote_folder: str | None
    latest_risk_level: str | None
    latest_score: int | None
    addresses: list[dict[str, Any]]
    attachments: list[dict[str, Any]]
    urls: list[dict[str, Any]]
    analysis_results: list[AnalysisResultRead]


class EmailAnalyzeResponse(BaseModel):
    email_id: str
    analysis_id: str
    risk_level: RiskLevel
    recommended_action: RecommendedAction
    total_score: int
    analyzer_results: list[AnalyzerOutput]


class EmailAnalyzeDeferredResponse(BaseModel):
    email_id: str
    status: str
    message: str
    component: str
