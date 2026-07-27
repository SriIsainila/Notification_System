from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("name", "phone", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def validate_bcrypt_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str | None = None
    created_at: datetime | None = None

    @classmethod
    def from_user(cls, user) -> "UserRead":
        return cls(
            id=user.user_id,
            name=user.full_name,
            email=user.email,
            phone=user.phone,
            created_at=user.created_at,
        )


class RegisterResponse(BaseModel):
    user: UserRead


class LoginResponse(BaseModel):
    user: UserRead


class TokenResponse(BaseModel):
    token: str
    user: UserRead


class CurrentUserResponse(BaseModel):
    user: UserRead


class LogoutResponse(BaseModel):
    message: str
