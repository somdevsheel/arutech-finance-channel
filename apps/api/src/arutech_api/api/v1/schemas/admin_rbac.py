import uuid

from pydantic import BaseModel


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    is_system: bool


class RoleCreateRequest(BaseModel):
    name: str
    description: str = ""


class PermissionResponse(BaseModel):
    id: uuid.UUID
    code: str
    description: str


class GrantPermissionRequest(BaseModel):
    permission_code: str
