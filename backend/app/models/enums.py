from enum import StrEnum

from sqlalchemy import Enum


class AddressRole(StrEnum):
    FROM = "from"
    REPLY_TO = "reply_to"
    RETURN_PATH = "return_path"
    TO = "to"
    CC = "cc"


class EmailSource(StrEnum):
    UPLOAD = "upload"
    API = "api"
    USER_REPORT = "user_report"


class EmailStatus(StrEnum):
    RECEIVED = "received"
    ANALYZED = "analyzed"
    ACTIONED = "actioned"


class MailboxProvider(StrEnum):
    QQ = "qq"
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    NETEASE_163 = "163"
    ALIYUN = "aliyun"
    CUSTOM = "custom"


class MailboxStatus(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    ERROR = "error"
    DISABLED = "disabled"


class SeverityLevel(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendedAction(StrEnum):
    ALLOW = "allow"
    BANNER_WARNING = "banner_warning"
    MOVE_TO_SPAM = "move_to_spam"
    QUARANTINE = "quarantine"
    MANUAL_REVIEW = "manual_review"


class AnalyzerExecutionStatus(StrEnum):
    SUCCESS = "success"
    SKIPPED = "skipped"
    ERROR = "error"


class IncidentStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


class ActionType(StrEnum):
    ALLOW = "allow"
    BANNER_WARNING = "banner_warning"
    MOVE_TO_SPAM = "move_to_spam"
    QUARANTINE = "quarantine"
    MANUAL_REVIEW = "manual_review"


class RuleConditionType(StrEnum):
    SUBJECT_CONTAINS = "subject_contains"
    SENDER_DOMAIN = "sender_domain"
    URL_CONTAINS = "url_contains"
    BODY_CONTAINS = "body_contains"


class RuleSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ListType(StrEnum):
    ADDRESS = "address"
    DOMAIN = "domain"
    URL = "url"


class AuditEventType(StrEnum):
    EMAIL_ANALYZED = "email_analyzed"
    EMAIL_REANALYZED = "email_reanalyzed"
    EMAIL_ACTIONED = "email_actioned"
    RULE_CREATED = "rule_created"
    RULE_UPDATED = "rule_updated"
    USER_REPORT_CREATED = "user_report_created"
    INCIDENT_CREATED = "incident_created"


class IssueSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


def sql_enum(enum_cls: type[StrEnum]) -> Enum:
    return Enum(
        enum_cls,
        native_enum=False,
        values_callable=lambda enum_type: [member.name for member in enum_type],
        length=max(len(member.name) for member in enum_cls),
    )
