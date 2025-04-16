"""
Unified Configuration Management System for AgentMate

This module provides a robust configuration management system with validation
using Pydantic models. It supports different types of configuration (app, database,
services, etc.) and loads values from environment variables and default values.
"""

import os
from typing import Dict, List, Optional, Any, Type, ClassVar, TypeVar
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, validator, root_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

from composio_openai import App

from DB.Schemas.gmail_config import GmailConfig

# Load environment variables from .env file
load_dotenv()

T = TypeVar('T', bound=BaseModel)


class LogLevel(str, Enum):
    """Log levels for the application."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", ""))
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 1800

    @validator('url')
    def validate_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL environment variable is required")
        return v


class RedisSettings(BaseModel):
    """Redis configuration settings."""
    url: str = Field(default="redis://localhost:6379/0")
    pool_size: int = 10
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True


class LoggingSettings(BaseModel):
    """Logging configuration settings."""
    enabled_levels: Dict[LogLevel, bool] = Field(
        default_factory=lambda: {
            LogLevel.DEBUG: True,
            LogLevel.INFO: True,
            LogLevel.WARNING: True,
            LogLevel.ERROR: True,
            LogLevel.FATAL: True
        }
    )
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class AsyncSettings(BaseModel):
    """Async processing configuration settings."""
    use_async: bool = True
    max_workers: int = 10
    task_timeout: int = 60


class ClassificationConfig(BaseModel):
    """Email classification configuration."""
    important_categories: List[str] = Field(
        default_factory=lambda: [
            "urgent", "meeting", "invoice", "payment due", "project update",
            "Github", "security alert", "password reset", "account verification",
            "legal notice", "deadline reminder", "contract", "shipping"
        ]
    )
    ignored_categories: List[str] = Field(
        default_factory=lambda: [
            "newsletter", "promotion", "social media", "spam", "survey",
            "event invitation", "job alert", "greetings"
        ]
    )


class GmailSettings(BaseModel):
    """Gmail service configuration settings."""
    client_secret: str = Field(default_factory=lambda: os.getenv("GOOGLE_CLIENT_SECRET", ""))
    redirect_uri: str = "https://omi-wroom.org/api/gmail/callback"
    scopes: List[str] = Field(
        default_factory=lambda: ["https://www.googleapis.com/auth/gmail.readonly"]
    )
    mail_check_interval: int = 60
    mail_count: int = 3
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)

    @validator('client_secret')
    def validate_client_secret(cls, v):
        if not v:
            raise ValueError("GOOGLE_CLIENT_SECRET environment variable is required for Gmail service")
        return v


class ServiceSettings(BaseModel):
    """Service-specific configuration settings."""
    gmail: GmailSettings = Field(default_factory=GmailSettings)
    # Add other services as needed
    # notion: NotionSettings = Field(default_factory=NotionSettings)


class ApiSettings(BaseModel):
    """API keys and related configuration."""
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    composio_api_key: str = Field(default_factory=lambda: os.getenv("COMPOSIO_API_KEY", ""))
    omi_api_key: str = Field(default_factory=lambda: os.getenv("OMI_API_KEY", ""))
    omi_app_id: str = Field(default_factory=lambda: os.getenv("OMI_APP_ID", ""))

    @validator('openai_api_key', 'composio_api_key', 'omi_api_key', 'omi_app_id')
    def validate_api_keys(cls, v, values, **kwargs):
        if not v:
            field_name = kwargs['field'].name
            raise ValueError(f"{field_name.upper()} environment variable is required")
        return v


class AppSettings(BaseSettings):
    """Main application settings."""
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
    service_apps: Dict[str, App] = Field(
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

    def get_service_config(self, service_name: str) -> Any:
        """Get configuration for a specific service."""
        if hasattr(self.services, service_name):
            return getattr(self.services, service_name)
        raise ValueError(f"No configuration found for service: {service_name}")

    def get_auth_provider_config(self, service_name: str) -> Dict[str, Any]:
        """Get authentication provider configuration for a service."""
        if service_name == "gmail":
            return {
                "client_secret": self.services.gmail.client_secret,
                "scopes": self.services.gmail.scopes,
                "redirect_uri": self.services.gmail.redirect_uri
            }
        # Add other services as needed
        raise ValueError(f"No auth provider configuration found for service: {service_name}")


# Create a global settings instance
settings = AppSettings()
