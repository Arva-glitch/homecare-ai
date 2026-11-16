from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.utils.time import UTCDateTime
from app.schemas.common import ORMModel


def _strong(pw: str) -> str:
    if len(pw) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not any(c.isdigit() for c in pw) or not any(c.isalpha() for c in pw):
        raise ValueError("Password must contain letters and numbers")
    return pw


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(max_length=72)
    household_name: str | None = Field(default=None, max_length=120)

    @field_validator("password")
    @classmethod
    def _pw(cls, v: str) -> str:
        return _strong(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    # Only populated in development when SMTP is not configured (see config).
    dev_reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    new_password: str = Field(max_length=72)

    @field_validator("new_password")
    @classmethod
    def _pw(cls, v: str) -> str:
        return _strong(v)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(max_length=72)

    @field_validator("new_password")
    @classmethod
    def _pw(cls, v: str) -> str:
        return _strong(v)


class UserOut(ORMModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    address: str | None
    household_name: str | None
    email_notifications: bool
    created_at: UTCDateTime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    household_name: str | None = Field(default=None, max_length=120)
    email_notifications: bool | None = None


TokenResponse.model_rebuild()
