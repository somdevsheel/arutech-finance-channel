import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PermissionEntity:
    id: uuid.UUID
    code: str
    description: str


@dataclass(frozen=True, slots=True)
class RoleEntity:
    id: uuid.UUID
    name: str
    description: str
    is_system: bool = False
