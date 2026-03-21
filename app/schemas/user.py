from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.base import SchemaBase


class UserOut(SchemaBase):
    id: int
    email: EmailStr
    created_at: datetime
    is_admin: bool = False


class UserMePasswordIn(SchemaBase):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class AdminUserPatchIn(SchemaBase):
    is_admin: bool | None = None


class UserListOut(SchemaBase):
    items: list[UserOut]
    total: int
    skip: int
    limit: int
