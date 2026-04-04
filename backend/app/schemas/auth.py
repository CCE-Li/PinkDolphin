from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    username: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_username: str
    current_password: str
    new_username: str
    new_password: str
