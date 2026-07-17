import uuid
from datetime import datetime

from pydantic import BaseModel

from arutech_api.domain.settings.entities import SettingValueType


class SystemSettingResponse(BaseModel):
    id: uuid.UUID
    key: str
    value: str
    value_type: SettingValueType
    description: str
    updated_at: datetime | None


class SystemSettingUpdateRequest(BaseModel):
    value: str
