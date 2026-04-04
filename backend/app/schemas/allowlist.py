from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ListType
from app.schemas.common import TimestampedSchema


class AllowlistBase(BaseModel):
    list_type: ListType
    value: str = Field(min_length=1, max_length=1024)
    is_active: bool = True
    skip_url_scan: bool = False
    skip_attachment_scan: bool = False
    skip_llm_scan: bool = False


class AllowlistCreate(AllowlistBase):
    pass


class AllowlistUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    list_type: ListType | None = None
    value: str | None = Field(default=None, min_length=1, max_length=1024)
    is_active: bool | None = None
    skip_url_scan: bool | None = None
    skip_attachment_scan: bool | None = None
    skip_llm_scan: bool | None = None


class AllowlistRead(TimestampedSchema):
    list_type: ListType
    value: str
    is_active: bool
    skip_url_scan: bool
    skip_attachment_scan: bool
    skip_llm_scan: bool
