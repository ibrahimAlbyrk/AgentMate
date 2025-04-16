"""
Data Transfer Objects (DTOs) for AgentMate

This module contains the DTOs used for API communication and data transfer
between components. DTOs are simple objects that don't contain business logic
but are used to transfer data between processes or across network boundaries.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

from Core.Models.domain import (
    AgentStatus, AgentHealth, SubscriberStatus, SubscriberHealth, EventType
)


# API Request/Response DTOs

class UserCreateRequest(BaseModel):
    """Request to create a new user."""
    email: str
    name: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class UserUpdateRequest(BaseModel):
    """Request to update a user."""
    email: Optional[str] = None
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class UserResponse(BaseModel):
    """Response containing user information."""
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    settings: Dict[str, Any] = Field(default_factory=dict)
    services: Dict[str, str] = Field(default_factory=dict)


class AgentCreateRequest(BaseModel):
    """Request to create a new agent."""
    user_id: str
    service_id: str
    service_name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class AgentUpdateRequest(BaseModel):
    """Request to update an agent."""
    status: Optional[AgentStatus] = None
    config: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Response containing agent information."""
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
    """Request to create a new subscriber."""
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)


class SubscriberUpdateRequest(BaseModel):
    """Request to update a subscriber."""
    status: Optional[SubscriberStatus] = None
    config: Optional[Dict[str, Any]] = None


class SubscriberResponse(BaseModel):
    """Response containing subscriber information."""
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
    """Request to create a new event."""
    type: EventType
    source: str
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EventResponse(BaseModel):
    """Response containing event information."""
    id: str
    type: EventType
    source: str
    timestamp: datetime
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskCreateRequest(BaseModel):
    """Request to create a new task."""
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    """Request to update a task."""
    status: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskResponse(BaseModel):
    """Response containing task information."""
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
    """Request to create a new service connection."""
    user_id: str
    service_name: str
    credentials: Dict[str, Any] = Field(default_factory=dict)


class ServiceConnectionUpdateRequest(BaseModel):
    """Request to update a service connection."""
    status: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None


class ServiceConnectionResponse(BaseModel):
    """Response containing service connection information."""
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
    """Update for agent status."""
    agent_id: str
    status: AgentStatus
    health: Optional[AgentHealth] = None
    last_active: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubscriberStatusUpdate:
    """Update for subscriber status."""
    subscriber_id: str
    status: SubscriberStatus
    health: Optional[SubscriberHealth] = None
    last_active: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskStatusUpdate:
    """Update for task status."""
    task_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceConnectionStatusUpdate:
    """Update for service connection status."""
    connection_id: str
    status: str
    last_used: Optional[datetime] = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)