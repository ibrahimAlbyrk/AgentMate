import json
import uuid
import time
from typing import Any, Dict, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Message:
    """
    Represents a message in the event bus system.

    A message contains a topic, payload, and optional metadata.
    """
    topic: str
    payload: Any
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """
        Convert the message to a JSON string.

        Returns:
            str: JSON representation of the message
        """
        return json.dumps(asdict(self), default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        """
        Create a Message instance from a JSON string.

        Args:
            json_str: JSON string representation of a message

        Returns:
            Message: A new Message instance
        """
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def create(cls, topic: str, payload: Any, **metadata) -> 'Message':
        """
        Create a new message with the given topic and payload.

        Args:
            topic: The topic of the message
            payload: The payload of the message
            **metadata: Additional metadata for the message

        Returns:
            Message: A new Message instance
        """
        return cls(topic=topic, payload=payload, metadata=metadata)