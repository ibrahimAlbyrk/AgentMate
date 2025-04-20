import os
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, ClassVar, TypeVar

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field, root_validator, field_validator, PrivateAttr

from composio_openai import App

from DB.Schemas.gmail_config import GmailConfig

load_dotenv()

T = TypeVar('T', bound=BaseModel)


class DatabaseSettings(BaseModel):
    url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800

    @field_validator('url')
    def validate_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL environment variable is required")
        return v


class RedisSettings(BaseModel):
    url: str = Field(default="redis://localhost:6379/0")
    pool_size: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True


class LoggingSettings(BaseModel):
    enabled_levels: Dict[int, bool] = Field(
        default_factory=lambda: {
            logging.DEBUG: True,
            logging.INFO: True,
            logging.WARNING: True,
            logging.ERROR: True,
            logging.FATAL: True
        }
    )
    log_file: Optional[str] = None


class AsyncSettings(BaseModel):
    max_workers: int = 10
    task_timeout: int = 60


class ClassificationConfig(BaseModel):
    default_important_categories: List[str] = Field(
        default_factory=lambda: [
            "urgent", "important", "asap", "reply needed", "action required",
            "meeting", "invoice", "billing", "payment",
            "project update", "task update", "delivery", "order",
            "github", "security", "password", "verification",
            "legal", "contract", "compliance",
            "deadline", "reminder", "support", "job interview", "application"
        ]
    )
    default_ignored_categories: List[str] = Field(
        default_factory=lambda: [
            "newsletter", "promotion", "social", "spam",
            "survey", "event", "job alert", "greetings",
            "notification", "update", "blog", "media"
        ]
    )


class GmailSettings(BaseModel):
    redirect_uri: str = "https://omi-wroom.org/api/gmail/callback"
    scopes: List[str] = Field(
        default_factory=lambda: ["https://www.googleapis.com/auth/gmail.readonly"]
    )
    mail_check_interval: int = 60
    mail_count: int = 3
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)


class ServiceSettings(BaseModel):
    gmail: GmailSettings = Field(default_factory=GmailSettings)
    # Add other services as needed
    # notion: NotionSettings = Field(default_factory=NotionSettings)


class ApiSettings(BaseModel):
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    composio_api_key: str = Field(default_factory=lambda: os.getenv("COMPOSIO_API_KEY", ""))
    omi_api_key: str = Field(default_factory=lambda: os.getenv("OMI_API_KEY", ""))
    omi_app_id: str = Field(default_factory=lambda: os.getenv("OMI_APP_ID", ""))

    @field_validator('openai_api_key', 'composio_api_key', 'omi_api_key', 'omi_app_id')
    def validate_api_keys(cls, v, values, **kwargs):
        if not v:
            field_name = kwargs['field'].name
            raise ValueError(f"{field_name.upper()} environment variable is required")
        return v


class AppSettings(BaseSettings):
    # General settings
    base_uri: str = "https://omi-wroom.org"
    token_path: str = "tokens/{service}/{uid}.pickle"
    post_login_redirect: str = "https://omi-wroom.org/{service}/settings?uid={uid}"

    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    async_settings: AsyncSettings = Field(default_factory=AsyncSettings)
    services: ServiceSettings = Field(default_factory=ServiceSettings)
    api: ApiSettings = Field(default_factory=ApiSettings)

    # Service mappings
    _service_apps: Dict[str, App] = PrivateAttr(
        default_factory=lambda: {"gmail": App.GMAIL}
    )

    # Configuration models for services
    config_models: Dict[str, Type[BaseModel]] = {
        "gmail": GmailConfig,
        # "notion": NotionConfig
    }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_config(self, config_name: str) -> dict[str, Any]:
        print(f"Getting config {config_name}")
        config_cls = self.get_config_model(config_name)
        if not config_cls:
            return {}

        print("return")
        return config_cls().model_dump()
    def get_config_model(self, config_name: str) -> Optional[Type[BaseModel]]:
        config_cls = self.config_models.get(config_name, None)
        if not config_cls:
            return None

        return config_cls

    def get_app(self, service_name: str) -> Optional[App]:
        return self._service_apps.get(service_name, "")

    def get_service_config(self, service_name: str) -> Any:
        if hasattr(self.services, service_name):
            return getattr(self.services, service_name)
        raise ValueError(f"No configuration found for service: {service_name}")

    def get_auth_provider_config(self, service_name: str) -> Dict[str, Any]:
        if service_name == "gmail":
            return {
                "redirect_uri": self.services.gmail.redirect_uri
            }
        raise ValueError(f"No auth provider configuration found for service: {service_name}")


settings = AppSettings()
