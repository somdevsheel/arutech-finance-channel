import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class UserRole(StrEnum):
    """Coarse actor type for Phase 1. Fine-grained RBAC (roles, permissions,
    role-bindings) is introduced in Phase 2 and will layer on top of this."""

    CUSTOMER = "customer"
    EMPLOYEE = "employee"
    PARTNER = "partner"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class UserEntity:
    """Framework-agnostic representation of a user, independent of the
    SQLAlchemy model that persists it or any HTTP schema that serializes it."""

    email: str
    hashed_password: str
    full_name: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    phone: str | None = None
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
