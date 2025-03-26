import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings:
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DATABASE_ECHO: bool = False

    # URLS
    BASE_URI: str = "https://omi-wroom.org"
    REDIS_URL: str = "redis://localhost:6379/0"
    POSTGRES_URI: str = "postgres://user:pass@host:port/dbname"

    # APP
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY")

    # OPEN AI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")

    # OMI
    OMI_API_KEY: str = os.getenv("OMI_API_KEY")
    OMI_APP_ID: str = os.getenv("OMI_APP_ID")

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

    class Config:
        env_file = ".env"


settings = Settings()
