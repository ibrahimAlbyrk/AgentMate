import os
import logging
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, ClassVar, TypeVar

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel, Field, root_validator, field_validator, PrivateAttr

from composio_openai import App

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


class GmailConfig(BaseModel):
    important_categories: List[str] = Field(
        default_factory=lambda: [
            "urgent", "important", "asap", "reply needed", "action required",
            "meeting", "invoice", "billing", "payment",
            "project update", "task update", "delivery", "order",
            "github", "security", "password", "verification",
            "legal", "contract", "compliance",
            "deadline", "reminder", "support", "job interview", "application"
        ]
    )
    ignored_categories: List[str] = Field(
        default_factory=lambda: [
            "newsletter", "promotion", "social", "spam",
            "survey", "job alert", "greetings",
            "blog"
        ]
    )

class NotionConfig(BaseModel):
    tracked_database_ids: List[str] = Field(
        default_factory=list,
    )

    tracked_page_types: List[str] = Field(
        default_factory=lambda: ["Task", "Note", "Meeting", "Project"],
    )


class ServiceSettings(BaseModel):
    gmail: GmailConfig = Field(default_factory=GmailConfig)
    notion: NotionConfig = Field(default_factory=NotionConfig)


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

    admin_token: str = os.getenv("ADMIN_TOKEN")

    # Open-ai
    gpt_model: str = "gpt-4.1-mini"

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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_app(self, service_name: str) -> Optional[App]:
        return self._service_apps.get(service_name, "")

    def get_service_config(self, service_name: str) -> dict[str, Any]:
        config_class = self.get_service_config_model(service_name)
        config_instance = config_class()
        return config_instance.model_dump()

    def get_service_config_model(self, service_name: str) -> Optional[Type[BaseModel]]:
        service_config_instance = getattr(self.services, service_name, None)
        if service_config_instance:
            return service_config_instance.__class__
        raise ValueError(f"No configuration found for service: {service_name}")

    def get_auth_provider_config(self, service_name: str) -> Dict[str, Any]:
        if service_name == "gmail":
            return {
                "redirect_uri": self.services.gmail.redirect_uri
            }
        raise ValueError(f"No auth provider configuration found for service: {service_name}")


settings = AppSettings()
