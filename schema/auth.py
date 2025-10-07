from pydantic import BaseModel


class RegisterRequest(BaseModel):
    user_id: str
    name: str | None = None
    email: str
    password: str
    phone: str | None = None
    role: str = "user"


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str
