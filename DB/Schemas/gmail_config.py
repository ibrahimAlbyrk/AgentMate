from typing import List
from pydantic import BaseModel


class GmailConfig(BaseModel):
    mail_check_interval: int = 60
    mail_count: int = 3
    important_categories: List[str] = []
    ignored_categories: List[str] = []