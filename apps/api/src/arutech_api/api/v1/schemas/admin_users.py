import uuid
from datetime import datetime

from pydantic import BaseModel

from arutech_api.domain.users.entities import UserRole


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    phone: str | None
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime | None
    updated_at: datetime | None


class SetRoleRequest(BaseModel):
    role: UserRole
