from datetime import datetime
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union

from Core.Models.domain import (
    AgentStatus, AgentHealth, SubscriberStatus, SubscriberHealth, EventType
)


# API Request/Response DTOs

class UserCreateRequest(BaseModel):
    email: str
    name: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = Field(default_factory=dict)
    services: Dict[str, str] = Field(default_factory=dict)


class AgentCreateRequest(BaseModel):
    user_id: str
    service_id: str
    service_name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdateRequest(BaseModel):
    status: Optional[AgentStatus] = None
    config: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    id: str
    user_id: str
    service_id: str
    service_name: str
    status: AgentStatus
    health: AgentHealth
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubscriberCreateRequest(BaseModel):
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class SubscriberUpdateRequest(BaseModel):
    status: Optional[SubscriberStatus] = None
    config: Optional[Dict[str, Any]] = None


class SubscriberResponse(BaseModel):
    id: str
    name: str
    status: SubscriberStatus
    health: SubscriberHealth
    created_at: datetime
    updated_at: datetime
    last_active: Optional[datetime] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventCreateRequest(BaseModel):
    type: EventType
    source: str
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    id: str
    type: EventType
    source: str
    timestamp: datetime
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskCreateRequest(BaseModel):
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServiceConnectionCreateRequest(BaseModel):
    user_id: str
    service_name: str
    credentials: Dict[str, Any] = Field(default_factory=dict)


class ServiceConnectionUpdateRequest(BaseModel):
    status: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None


class ServiceConnectionResponse(BaseModel):
    id: str
    user_id: str
    service_name: str
    status: str
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# Internal DTOs for component communication

@dataclass
class AgentStatusUpdate:
    agent_id: str
    status: AgentStatus
    health: Optional[AgentHealth] = None
    last_active: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubscriberStatusUpdate:
    subscriber_id: str
    status: SubscriberStatus
    health: Optional[SubscriberHealth] = None
    last_active: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskStatusUpdate:
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceConnectionStatusUpdate:
    connection_id: str
    status: str
    last_used: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)