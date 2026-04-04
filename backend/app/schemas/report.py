from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserReportCreate(BaseModel):
    reporter_email: str
    reporter_name: str | None = None
    reason: str
    email_id: str | None = None
    raw_email: str | None = None


class UserReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email_id: str | None
    reporter_email: str
    reporter_name: str | None
    reason: str
    raw_email: str | None
    resolved: bool
    created_at: datetime
    updated_at: datetime
