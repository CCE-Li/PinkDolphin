from pydantic import BaseModel


class EnvFileRead(BaseModel):
    path: str
    content: str
    editable_keys: list[str]


class EnvFileUpdate(BaseModel):
    content: str
