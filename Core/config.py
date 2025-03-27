import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from DB.Schemas.gmail_config import GmailConfig

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

    # GOOGLE
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = "https://omi-wroom.org/gmail/callback"
    GOOGLE_GMAIL_SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
    ]

    TOKEN_PATH = "tokens/{service}/{uid}.pickle"
    POST_LOGIN_REDIRECT = "http://localhost/{service}/settings?uid={uid}"

    AUTH_PROVIDERS: dict[str, dict] = {
        "gmail": {
            "client_secret": GOOGLE_CLIENT_SECRET,
            "scopes": GOOGLE_GMAIL_SCOPES,
            "redirect_uri": GOOGLE_REDIRECT_URI
        }
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
