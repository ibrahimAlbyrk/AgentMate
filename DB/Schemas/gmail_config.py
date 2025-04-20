from typing import List
from pydantic import BaseModel


class GmailConfig(BaseModel):
    important_categories: List[str] = []
    ignored_categories: List[str] = []