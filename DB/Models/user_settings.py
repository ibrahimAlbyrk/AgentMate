from datetime import datetime
from DB.Models.base import BaseModel
from sqlalchemy import Column, String, JSON, DateTime, PrimaryKeyConstraint

class UserSettings(BaseModel):
    __tablename__ = "user_settings"

    uid = Column(String, nullable=False)
    service_name = Column(String, nullable=False)

    is_logged_in = Column(Boolean, default=False)
    token_path = Column(String, nullable=True)

    config = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    __table_args__ = (
        PrimaryKeyConstraint('uid', 'service_name', name='pk_user_settings'),
    )