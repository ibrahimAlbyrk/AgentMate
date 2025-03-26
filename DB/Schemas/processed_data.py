from pydantic import BaseModel
from datetime import datetime


class ProcessedDateBase(BaseModel):
    uid: str
    service: str
    data_type: str
    content: str


class ProcessedDataCreate(ProcessedDateBase):
    pass


class ProcessedDataOut(ProcessedDateBase):
    created_at: datetime

    class Config:
        orm_mode = True