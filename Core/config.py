import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from DB.Schemas.gmail_config import GmailConfig

from composio_openai import App

load_dotenv()


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_ECHO: bool = False

    # URLS
    BASE_URI: str = "https://omi-wroom.org"
    REDIS_URL: str = "redis://localhost:6379/0"
    POSTGRES_URI: str = "postgres://user:pass@host:port/dbname"

    # OPEN AI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    # OMI
    OMI_API_KEY: str = os.getenv("OMI_API_KEY")
    OMI_APP_ID: str = os.getenv("OMI_APP_ID")

    # COMPOSIO
    COMPOSIO_API_KEY: str = os.getenv("COMPOSIO_API_KEY")

    TOKEN_PATH = "tokens/{service}/{uid}.pickle"
    POST_LOGIN_REDIRECT = "https://omi-wroom.org/{service}/settings?uid={uid}"

    SERVICES: dict[str, App] = {
        "gmail": App.GMAIL
    }

    # ASYNC
    USE_ASYNC: bool = True
    MAX_TASK_WORKER: int = 10

    # LOGGING
    LOG_STATES: dict[str, bool] = {
        "debug": True,
        "info": True,
        "warning": True,
        "error": True,
        "fatal": True
    }

    class ClassificationConfig:
        DEFAULT_IMPORTANT_CATEGORIES = [
            "urgent", "meeting", "invoice", "payment due", "project update",
            "Github", "security alert", "password reset", "account verification",
            "legal notice", "deadline reminder", "contract", "shipping"
        ]
        DEFAULT_IGNORED_CATEGORIES = [
            "newsletter", "promotion", "social media", "spam", "survey",
            "event invitation", "job alert", "greetings"
        ]

    DEFAULT_CONFIGS = {
        "gmail": {
            "mail_check_interval": 60,
            "mail_count": 3,
            "important_categories": ClassificationConfig.DEFAULT_IMPORTANT_CATEGORIES,
            "ignored_categories": ClassificationConfig.DEFAULT_IGNORED_CATEGORIES,
        },
    }

    CONFIG_MODELS = {
        "gmail": GmailConfig,
        # "notion": NotionConfig
    }

    class Config:
        env_file = ".env"


settings = Settings()
