from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_emails: int
    analyzed_emails: int
    open_incidents: int
    critical_emails: int
    high_risk_emails: int
    monitored_mailboxes: int
    listening_mailboxes: int
    mailbox_errors: int
