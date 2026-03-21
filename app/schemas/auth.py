from pydantic import EmailStr, Field

from app.schemas.base import SchemaBase


class RegisterIn(SchemaBase):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginIn(SchemaBase):
    email: EmailStr
    password: str


class TokenPairOut(SchemaBase):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshIn(SchemaBase):
    refresh_token: str
