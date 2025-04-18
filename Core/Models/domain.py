from enum import Enum
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


class AgentHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class SubscriberStatus(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    ERROR = "error"
    STOPPED = "stopped"


class SubscriberHealth(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    START_AGENT = "start_agent"
    START_ALL_AGENT = "start_all_agent"
    STOP_AGENT = "stop_agent"
    STOP_ALL_AGENT = "stop_all_agent"
    RESTART_AGENT = "restart_agent"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    SUBSCRIBER_STARTED = "subscriber_started"
    SUBSCRIBER_STOPPED = "subscriber_stopped"
    SUBSCRIBER_ERROR = "subscriber_error"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_PROCESSED = "message_processed"
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"


@dataclass
class User:
    id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    settings: Dict[str, Any] = field(default_factory=dict)
    services: Dict[str, str] = field(default_factory=dict)


@dataclass
class Agent:
    """
    Represents an agent in the system.

    An agent is a component that performs tasks for a user,
    such as processing emails or managing calendar events.
    """
    id: str
    user_id: str
    service_id: str
    service_name: str
    status: AgentStatus = AgentStatus.IDLE
    health: AgentHealth = AgentHealth.UNKNOWN
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Subscriber:
    """
    Represents a subscriber in the system.

    A subscriber listens for events and performs actions in response.
    """
    id: str
    name: str
    status: SubscriberStatus = SubscriberStatus.IDLE
    health: SubscriberHealth = SubscriberHealth.UNKNOWN
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_active: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    """
    Represents an event in the system.

    Events are used for communication between components.
    """
    id: str
    type: EventType
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """
    Represents a task in the system.

    Tasks are units of work that are executed asynchronously.
    """
    id: str
    name: str
    status: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """
    Represents a message in the system.

    Messages are used for communication between components.
    """
    id: str
    topic: str
    content: Any
    sender: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceConnection:
    """
    Represents a connection to an external service.

    Service connections are used to interact with external services
    such as Gmail, Calendar, etc.
    """
    id: str
    user_id: str
    service_name: str
    status: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    credentials: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)