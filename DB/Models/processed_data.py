from datetime import datetime
from DB.Models.base import BaseModel
from sqlalchemy import Column, String, DateTime, Text, PrimaryKeyConstraint

class ProcessedData(BaseModel):
    __tablename__ = "processed_data"

    uid = Column(String, nullable=False)
    service = Column(String, nullable=False)
    data_type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (
        PrimaryKeyConstraint('uid', 'service', 'data_type', name='pk_processed_data'),
    )