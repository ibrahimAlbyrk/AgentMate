from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class UserSettingsBase(BaseModel):
    uid: str
    service_name: str

    service_id: str

    is_logged_in: bool
    token_path: str

    config: Optional[dict] = None


class UserSettingsCreate(UserSettingsBase):
    pass


class UserSettingsUpdate(UserSettingsBase):
    config: Optional[dict] = None


class UserSettingsOut(UserSettingsBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
